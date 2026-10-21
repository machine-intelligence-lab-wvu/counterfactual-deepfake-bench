#!/usr/bin/env python
"""Render a batch into a frozen view. One script for reals and fakes.

  python -m eval.preprocess --view face512 --batch fake_b1 [--shard 0 --nshards 8] [--workers 36]

Per source clip:
  - trim to the view's 5.0 s segment (fakes: start; reals: middle, excluded if shorter)
  - fakes keep native fps; reals are rendered at every fps in the spec (clip_id__fps24, ...)
  - geometry: native = passthrough (source must equal 1280x704); face512 = scale-to-cover then
    one fixed 512x512 window at the median YuNet face centre, shifted inward at frame edges
  - encode with the pinned ffmpeg/x264 recipe, then verify the output with ffprobe

Every attempt is a record (status ok / excluded / failed) appended to
results/preprocess/<view>/<batch>/part-*.parquet; nothing is dropped silently. A rerun skips
outputs already recorded ok or excluded under the same view_hash, and retries failures.
"""
import argparse
import glob
import json
import math
import os
import subprocess
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction

import numpy as np
import pandas as pd

from eval.common import (FFMPEG, FFPROBE, REPO, RESULTS, VIEWS_ROOT, WEIGHTS, batch_info,
                         git_commit, sha256_file, utc_now)
from eval.views.spec import load as load_view

_DET = {}


# ---------------------------------------------------------------- probing / verification
def probe(path, count_frames=False):
    cmd = [FFPROBE, "-v", "error", "-print_format", "json", "-show_streams", "-show_format"]
    if count_frames:
        cmd.insert(1, "-count_frames")
    info = json.loads(subprocess.run(cmd + [path], capture_output=True, text=True,
                                     check=True).stdout)
    v = [s for s in info["streams"] if s["codec_type"] == "video"]
    if not v:
        raise ValueError("no video stream")
    v = v[0]
    fps = Fraction(v["avg_frame_rate"]) if v.get("avg_frame_rate", "0/0") != "0/0" \
        else Fraction(v["r_frame_rate"])
    dur = float(v.get("duration") or info["format"].get("duration") or 0.0)
    return {"width": int(v["width"]), "height": int(v["height"]), "fps": fps,
            "duration": dur, "codec_name": v["codec_name"], "pix_fmt": v.get("pix_fmt"),
            "nb_frames": int(v.get("nb_read_frames") or v.get("nb_frames") or 0),
            "n_audio": sum(s["codec_type"] == "audio" for s in info["streams"]),
            "n_streams": len(info["streams"]), "tags": info["format"].get("tags", {})}


def keyframe_times(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-skip_frame",
                          "nokey", "-show_entries", "frame=pts_time", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return [float(x.split(",")[0]) for x in out.split() if x.split(",")[0].strip()]


def verify(path, spec, fps, size):
    """Return a list of problems (empty = output conforms to the view)."""
    p = probe(path, count_frames=True)
    want_frames = round(spec["duration_s"] * fps)
    probs = []
    if p["codec_name"] != "h264":
        probs.append(f"codec {p['codec_name']}")
    if p["pix_fmt"] != spec["encode"]["pix_fmt"]:
        probs.append(f"pix_fmt {p['pix_fmt']}")
    if (p["width"], p["height"]) != size:
        probs.append(f"size {p['width']}x{p['height']} != {size[0]}x{size[1]}")
    if p["fps"] != fps:
        probs.append(f"fps {p['fps']} != {fps}")
    if p["nb_frames"] != want_frames:
        probs.append(f"frames {p['nb_frames']} != {want_frames}")
    if p["n_audio"] or p["n_streams"] != 1:
        probs.append(f"streams {p['n_streams']} (audio {p['n_audio']})")
    kt = keyframe_times(path)
    gop = spec["encode"]["gop_seconds"]
    want_kt = [k * gop for k in range(math.ceil(spec["duration_s"] / gop))]
    if len(kt) != len(want_kt) or any(abs(a - b) > 0.5 / float(fps) for a, b in zip(kt, want_kt)):
        probs.append(f"keyframes {kt} != {want_kt}")
    return probs, p


# ---------------------------------------------------------------- face window
def yunet(w, h, spec):
    import cv2
    fd = spec["geometry"]["face_detector"]
    if "det" not in _DET:
        path = os.path.join(WEIGHTS, "yunet", fd["file"])
        if sha256_file(path) != fd["sha256"]:
            raise RuntimeError(f"YuNet checksum mismatch: {path}")
        _DET["det"] = cv2.FaceDetectorYN.create(path, "", (w, h), fd["score_threshold"],
                                                fd["nms_threshold"], 5000)
    _DET["det"].setInputSize((w, h))
    return _DET["det"]


def face_centre(path, start, n_frames, spec):
    """Median subject-face centre over the segment, in source pixels.

    Subject = largest detected face per frame (qc/faces.py rule). Returns (cx, cy, n_with_face,
    n_scanned, median_face_h)."""
    import av
    import cv2
    fd = spec["geometry"]["face_detector"]
    cxs, cys, hs, n = [], [], [], 0
    with av.open(path) as c:
        s = c.streams.video[0]
        if start > 0:
            c.seek(int(start / s.time_base), stream=s, backward=True, any_frame=False)
        for fr in c.decode(s):
            t = float(fr.pts * s.time_base) if fr.pts is not None else 0.0
            if t + 1e-6 < start:
                continue
            if n >= n_frames:
                break
            img = fr.to_ndarray(format="bgr24")
            det = yunet(img.shape[1], img.shape[0], spec)
            _, faces = det.detect(img)
            n += 1
            if faces is None:
                continue
            fs = [f for f in faces if f[3] >= fd["min_face_px"]]
            if not fs:
                continue
            f = max(fs, key=lambda f: f[3])
            cxs.append(f[0] + f[2] / 2)
            cys.append(f[1] + f[3] / 2)
            hs.append(f[3])
    if not cxs:
        return None, None, 0, n, 0.0
    return float(np.median(cxs)), float(np.median(cys)), len(cxs), n, float(np.median(hs))


def window(src_w, src_h, cx, cy, size):
    """Scale-to-cover + fixed window, shifted inward at the edges."""
    s = size / min(src_w, src_h)
    W2, H2 = round(src_w * s), round(src_h * s)
    want_x, want_y = cx * W2 / src_w - size / 2, cy * H2 / src_h - size / 2
    x0 = int(min(max(round(want_x), 0), W2 - size))
    y0 = int(min(max(round(want_y), 0), H2 - size))
    return W2, H2, x0, y0, int(abs(x0 - round(want_x))), int(abs(y0 - round(want_y)))


# ---------------------------------------------------------------- one clip
def outputs_for(row, kind, spec, view_root):
    """(out_id, start_s, out_fps or None for native) per output of one source clip."""
    if kind == "fake":
        return [(row["clip_id"], None)]
    return [(f"{row['clip_id']}__fps{f}", f) for f in spec["fps"]["real"]]


def process(task):
    row, kind, spec, out_id, out_fps, out_path = task
    t0 = time.time()
    rec = {"clip_id": out_id, "source_clip_id": row["clip_id"], "batch": row["batch"],
           "view": spec["name"], "view_hash": spec["view_hash"], "out_path": out_path,
           "status": "failed", "error": "", "start_s": 0.0, "out_fps": "", "face_cx": np.nan,
           "face_cy": np.nan, "face_h": np.nan, "face_frames": 0, "frames_scanned": 0,
           "win_x": -1, "win_y": -1, "shifted_x": 0, "shift_x_px": 0, "shifted_y": 0,
           "shift_y_px": 0, "src_width": 0,
           "src_height": 0, "src_fps": "", "src_duration": 0.0, "verify": "",
           "timestamp": utc_now(), "git_commit": "", "seconds": 0.0}
    try:
        src = probe(row["path"])
        rec.update(src_width=src["width"], src_height=src["height"], src_fps=str(src["fps"]),
                   src_duration=round(src["duration"], 3))
        D = spec["duration_s"]
        if src["duration"] + 1e-3 < D:
            rec.update(status="excluded", error=f"shorter than {D}s")
            return rec
        start = 0.0 if spec["trim"][kind] == "start" else round((src["duration"] - D) / 2, 3)
        fps = src["fps"] if out_fps is None else Fraction(out_fps)
        rec.update(start_s=start, out_fps=str(fps))
        g = spec["geometry"]
        if g["mode"] == "passthrough":
            if (src["width"], src["height"]) != (g["width"], g["height"]):
                rec.update(status="excluded",
                           error=f"source {src['width']}x{src['height']} != {g['width']}x{g['height']}")
                return rec
            vf, size = [], (g["width"], g["height"])
        else:
            S = g["size"]
            if min(src["width"], src["height"]) < S:
                rec.update(status="excluded", error=f"shorter side < {S} (never upscale)")
                return rec
            n_seg = round(D * float(src["fps"]))
            cx, cy, nf, ns, fh = face_centre(row["path"], start, n_seg, spec)
            rec.update(face_frames=nf, frames_scanned=ns)
            if cx is None:
                rec.update(status="excluded", error=f"no face in {ns} frames")
                return rec
            W2, H2, x0, y0, sx, sy = window(src["width"], src["height"], cx, cy, S)
            # a window spanning the full short side cannot move along it, so that axis
            # always "shifts"; both axes are logged, the long-axis count is the informative one
            rec.update(face_cx=round(cx, 1), face_cy=round(cy, 1), face_h=round(fh, 1),
                       win_x=x0, win_y=y0, shifted_x=int(sx > 0), shift_x_px=sx,
                       shifted_y=int(sy > 0), shift_y_px=sy)
            vf = [f"scale={W2}:{H2}:flags={g['scale_flags']}", f"crop={S}:{S}:{x0}:{y0}"]
            size = (S, S)
        if out_fps is not None:
            vf.insert(0, f"fps={out_fps}")
        if start > 0:
            # an input seek that lands between source frames leaves the first frame at a
            # small positive pts; fps= then shifts every output frame by one and the
            # keyframe/frame-count checks fail. Re-zero after the seek. Fakes start at 0.
            vf.insert(0, "setpts=PTS-STARTPTS")
        vf.append("setsar=1")
        enc = spec["encode"]
        gop = round(enc["gop_seconds"] * float(fps))
        n_out = round(D * float(fps))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        tmp = out_path + ".tmp.mp4"
        cmd = [FFMPEG, "-nostdin", "-hide_banner", "-loglevel", "error", "-y"]
        if start > 0:
            cmd += ["-ss", f"{start:.3f}"]
        cmd += ["-i", row["path"], "-map", "0:v:0", "-vf", ",".join(vf), "-frames:v", str(n_out),
                "-c:v", enc["codec"], "-preset", enc["preset"], "-crf", str(enc["crf"]),
                "-pix_fmt", enc["pix_fmt"], "-g", str(gop), "-keyint_min", str(gop),
                "-sc_threshold", str(enc["sc_threshold"]), "-threads", str(enc["threads"]),
                "-an", "-sn", "-dn"]
        if enc["strip_metadata"]:
            cmd += ["-map_metadata", "-1", "-map_chapters", "-1"]
        if enc["bitexact"]:
            cmd += ["-fflags", "+bitexact", "-flags:v", "+bitexact"]
        cmd += [tmp]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"ffmpeg exit {r.returncode}: {r.stderr.strip()[-400:]}")
        probs, p = verify(tmp, spec, fps, size)
        rec["verify"] = json.dumps({"frames": p["nb_frames"], "fps": str(p["fps"]),
                                    "size": f"{p['width']}x{p['height']}", "problems": probs})
        if probs:
            os.remove(tmp)
            raise RuntimeError("verify: " + "; ".join(probs))
        os.replace(tmp, out_path)
        rec["status"] = "ok"
    except Exception as e:
        rec.update(status="failed", error=f"{type(e).__name__}: {e}"[:600])
        if os.environ.get("FAIRDEEP_DEBUG"):
            traceback.print_exc()
    finally:
        rec["seconds"] = round(time.time() - t0, 2)
    return rec


# ---------------------------------------------------------------- records
def records_dir(view, batch):
    return os.path.join(RESULTS, "preprocess", view, batch)


def read_records(view, batch):
    parts = sorted(glob.glob(os.path.join(records_dir(view, batch), "part-*.parquet")))
    if not parts:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)


def latest_records(view, batch, view_hash=None):
    df = read_records(view, batch)
    if df.empty:
        return df
    if view_hash:
        df = df[df["view_hash"] == view_hash]
    return df.sort_values("timestamp").groupby("clip_id", as_index=False).tail(1)


def export(view, batch, view_hash):
    """Small committed CSV: latest record per output clip under the current view hash."""
    df = latest_records(view, batch, view_hash)
    if df.empty:
        return None
    out = os.path.join(records_dir(view, batch) + ".csv")
    df.drop(columns=["out_path"]).sort_values("clip_id").to_csv(out, index=False)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--shard", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_ID", 0)))
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-ids", default=None, help="file with one clip_id per line")
    a = ap.parse_args()

    spec = load_view(a.view)
    info = batch_info(a.batch)
    man = pd.read_csv(os.path.join(REPO, info["manifest"]), dtype={"clip_id": str})
    if a.only_ids:
        keep = set(open(a.only_ids).read().split())
        man = man[man["clip_id"].isin(keep)]
    man = man.sort_values("clip_id").iloc[a.shard::a.nshards]
    if a.limit:
        man = man.head(a.limit)

    done = latest_records(a.view, a.batch, spec["view_hash"])
    done = {} if done.empty else dict(zip(done["clip_id"], done["status"]))
    root = os.path.join(VIEWS_ROOT, a.view, spec["view_hash"], a.batch)
    tasks, skipped = [], 0
    for row in man.to_dict("records"):
        for out_id, out_fps in outputs_for(row, info["kind"], spec, root):
            out_path = os.path.join(root, out_id + ".mp4")
            st = done.get(out_id)
            if st == "excluded" or (st == "ok" and os.path.exists(out_path)):
                skipped += 1
                continue
            tasks.append((row, info["kind"], spec, out_id, out_fps, out_path))
    print(f"{a.view}/{a.batch} shard {a.shard}/{a.nshards}: {len(tasks)} to render, "
          f"{skipped} already done, {a.workers} workers -> {root}", flush=True)
    if not tasks:
        return
    commit = git_commit()
    recs, t0 = [], time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(process, t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            r["git_commit"] = commit
            r["ffmpeg_version"] = spec["toolchain"]["ffmpeg_version"]
            recs.append(r)
            if i % 100 == 0 or i == len(futs):
                c = pd.Series([x["status"] for x in recs]).value_counts().to_dict()
                print(f"  {i}/{len(futs)} {c} {time.time() - t0:.0f}s", flush=True)
    os.makedirs(records_dir(a.view, a.batch), exist_ok=True)
    part = os.path.join(records_dir(a.view, a.batch),
                        f"part-{utc_now().replace(':', '')}-{os.environ.get('SLURM_JOB_ID', 'local')}"
                        f"-s{a.shard}.parquet")
    pd.DataFrame(recs).to_parquet(part, index=False)
    out = export(a.view, a.batch, spec["view_hash"])
    df = pd.DataFrame(recs)
    print(f"wrote {part}\nexport {out}\nstatus {df['status'].value_counts().to_dict()} "
          f"shifted_x {int(df['shifted_x'].sum())} shifted_y {int(df['shifted_y'].sum())}")
    for r in df[df["status"] == "failed"].head(5).itertuples():
        print(f"  FAILED {r.clip_id}: {r.error}")


if __name__ == "__main__":
    main()
