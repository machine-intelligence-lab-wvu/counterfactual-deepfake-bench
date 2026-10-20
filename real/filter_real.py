"""Filter real footage into clips that match the synthetic half's spec.

The synthetic clips are not a loose collection - they are 1280x704,
single-subject, head-and-shoulders, face centred. A real half that differs on
any of those is not a control: a detector can separate the halves on framing or
resolution alone and never look at a face. So this does not merely *accept or
reject* real video, it *conforms* it, and records every conformance it applied
so the cost is visible in analysis rather than hidden in the pixels.

Targets are measured from the 3,936 QC-passing synthetic clips, not guessed:

    face height / frame height   p10 0.54   median 0.68   p90 0.80
    face centre x                p10 0.36   median 0.49   p90 0.57
    resolution                   1280x704 everywhere

Length and sharpness are deliberately *not* matched. 6.04 s was a generation
rule, and comparisons trim clips to several lengths, so each real clip keeps its
whole clean run (at least --min-dur) and analysis cuts it to whatever length a
comparison needs. Blur is a property of real footage and stays in;
--min-sharpness exists for a strict subset but is off by default. Brightness is
gated only against black frames, the same single check qc/scan.py applies to the
synthetic half - the synthetic lighting bank includes low-light and backlit
scenes on purpose, and dropping dim real clips would remove exactly the
lighting x skin-tone conditions the benchmark is built to probe.

Two deliberate non-conformances, both recorded per clip rather than resolved:

  - fps is left at the source rate. P0 section 5.1 settled this for the
    generators (LTX 24, Wan 16) on the grounds that resampling introduces its
    own detectable artifacts; resampling the real half would be the same
    mistake. fps is a declared per-source property.
  - upscaling is permitted up to --max-upscale, because a real face large
    enough to crop 704 lines natively is rarer than it sounds. `upscale` is a
    column in the report: tighten it to 1.0 for a strict subset.

    python real/filter_real.py --videos <dir> --out-root <dir>
"""
import argparse, csv, glob, json, os, subprocess, sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qc"))
from faces import (BG_MIN_FRAMES, MIN_FACE_PX, PERSON_SCORE,  # noqa: E402
                   SCORE as YUNET_SCORE)

TARGET_W, TARGET_H = 1280, 704
ASPECT = TARGET_W / TARGET_H              # 1.8182
MIN_DUR = 2.0                             # shortest clean run kept; not a target length

FACE_FRAC_TARGET = 0.68                   # face height as a fraction of frame height
FACE_FRAC_MIN, FACE_FRAC_MAX = 0.54, 0.80
FACE_CY_TARGET = 0.42                     # head-and-shoulders: eyes above centre

SCAN_FPS = 4.0                            # face/quality sampling rate during the scan
FROZEN_RAW = 0.30                         # from qc/scan.py, same meaning
BLACK_MEAN = 8.0
MIN_SHARPNESS = 0.0                       # off: blur is real-footage signal, not a defect

_det = {}


def detector(w, h, model):
    if "d" not in _det:
        _det["d"] = cv2.FaceDetectorYN.create(model, "", (w, h), YUNET_SCORE, 0.3, 5000)
        _det["wh"] = (w, h)
    if _det["wh"] != (w, h):
        _det["d"].setInputSize((w, h))
        _det["wh"] = (w, h)
    return _det["d"]


def yunet_model(cache_dir):
    """YuNet ONNX, fetched once. Same model and thresholds as qc/faces.py."""
    d = Path(cache_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "face_detection_yunet_2023mar.onnx"
    if not p.exists():
        import urllib.request
        url = ("https://huggingface.co/opencv/face_detection_yunet/resolve/main/"
               "face_detection_yunet_2023mar.onnx")
        tmp = p.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(p)
    return str(p)


def _overlaps(a, b):
    return not (a[0] > b[0] + b[2] or a[0] + a[2] < b[0] or
                a[1] > b[1] + b[3] or a[1] + a[3] < b[1])


def scan(path, model, scan_fps=SCAN_FPS):
    """Walk the clip once, recording face geometry and frame quality per sample."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None, "unreadable"
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if fps <= 0 or n <= 0 or w <= 0 or h <= 0:
        cap.release()
        return None, "bad header"

    step = max(1, int(round(fps / scan_fps)))
    samples, prev = [], None
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i % step == 0:
            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            det = detector(w, h, model)
            _, faces = det.detect(frame)
            fs = [] if faces is None else sorted(
                (f for f in faces if f[3] >= MIN_FACE_PX), key=lambda f: -f[3])
            rec = {"i": i, "t": i / fps,
                   "luma": float(g.mean()), "contrast": float(g.std()),
                   "sharp": float(cv2.Laplacian(g, cv2.CV_64F).var()),
                   "diff": float(np.abs(g.astype(np.float32) -
                                        prev.astype(np.float32)).mean()) if prev is not None else None}
            if fs:
                s = fs[0]
                others = [f for f in fs[1:] if f[-1] >= PERSON_SCORE and not _overlaps(f, s)]
                rec.update(face=True, fx=float(s[0]), fy=float(s[1]),
                           fw=float(s[2]), fh=float(s[3]), fscore=float(s[-1]),
                           n_others=len(others))
            else:
                rec.update(face=False, n_others=0)
            samples.append(rec)
            prev = g
        i += 1
    cap.release()
    return {"fps": fps, "n_frames": n, "w": w, "h": h, "dur": n / fps,
            "samples": samples}, None


def pick_window(sc, min_dur, max_upscale, min_sharp):
    """Longest-scoring run of samples that is one person, in frame, and usable.

    A clip is accepted on a *window*, not on its average: real footage cuts, pans
    and lets second people walk through, and a clip with six clean seconds in the
    middle is worth keeping. The window must satisfy every gate at every sample
    it covers - averaging here would let a two-second dropout hide inside a good
    mean.
    """
    s = sc["samples"]
    H = sc["h"]
    good = []
    for r in s:
        ok = (r["face"] and r["n_others"] == 0
              and r["luma"] >= BLACK_MEAN
              and r["sharp"] >= min_sharp)
        if ok:
            # the crop this sample would need must not over-upscale
            crop_h = r["fh"] / FACE_FRAC_TARGET
            ok = (TARGET_H / crop_h) <= max_upscale and crop_h <= H * 1.6
        good.append(ok)

    if not any(good):
        return None, _why(s, good)

    best, run_start = None, None
    for idx in range(len(s) + 1):
        alive = idx < len(s) and good[idx]
        if alive and run_start is None:
            run_start = idx
        elif not alive and run_start is not None:
            a, b = run_start, idx - 1
            span = s[b]["t"] - s[a]["t"]
            if span >= min_dur:
                # keep the longest clean run; comparisons trim to their own lengths
                if best is None or span > best[2]:
                    best = (a, b, span)
            run_start = None

    if best is None:
        return None, "no clean run of %.2fs" % min_dur
    a, b, _ = best
    run = s[a:b + 1]
    fh = float(np.median([r["fh"] for r in run]))
    fcx = float(np.median([r["fx"] + r["fw"] / 2 for r in run]))
    fcy = float(np.median([r["fy"] + r["fh"] / 2 for r in run]))
    return {"start_t": s[a]["t"], "end_t": s[b]["t"], "dur": s[b]["t"] - s[a]["t"],
            "n_samples": len(run),
            "face_h": fh, "face_cx": fcx, "face_cy": fcy,
            "sharp": float(np.median([r["sharp"] for r in run])),
            "luma": float(np.median([r["luma"] for r in run])),
            "contrast": float(np.median([r["contrast"] for r in run])),
            "motion_raw": float(np.mean([r["diff"] for r in run if r["diff"] is not None]) or 0.0),
            }, None


def _why(samples, good):
    if not samples:
        return "no frames"
    if not any(r["face"] for r in samples):
        return "no face detected"
    if sum(r["n_others"] > 0 for r in samples) >= BG_MIN_FRAMES:
        return "background people"
    if MIN_SHARPNESS > 0 and all(r["sharp"] < MIN_SHARPNESS for r in samples if r["face"]):
        return "too soft"
    return "face too small or frame unusable"


def crop_box(win, sc, max_upscale):
    """Crop rectangle that puts the face at the synthetic half's size and position."""
    W, H = sc["w"], sc["h"]
    crop_h = win["face_h"] / FACE_FRAC_TARGET
    crop_w = crop_h * ASPECT

    if crop_w > W:                      # portrait or narrow source: width-limited
        crop_w = float(W)
        crop_h = crop_w / ASPECT
    if crop_h > H:
        crop_h = float(H)
        crop_w = crop_h * ASPECT
        if crop_w > W:
            return None, "source too narrow for 16:8.8 crop"

    x = win["face_cx"] - crop_w / 2
    y = win["face_cy"] - crop_h * FACE_CY_TARGET
    x = max(0.0, min(x, W - crop_w))
    y = max(0.0, min(y, H - crop_h))

    frac = win["face_h"] / crop_h
    if not (FACE_FRAC_MIN <= frac <= FACE_FRAC_MAX):
        return None, f"face fraction {frac:.2f} outside [{FACE_FRAC_MIN},{FACE_FRAC_MAX}]"
    up = TARGET_H / crop_h
    if up > max_upscale:
        return None, f"needs {up:.2f}x upscale"

    # even numbers keep libx264 happy
    return {"x": int(x) // 2 * 2, "y": int(y) // 2 * 2,
            "w": int(crop_w) // 2 * 2, "h": int(crop_h) // 2 * 2,
            "face_frac": round(frac, 3), "upscale": round(up, 3)}, None


def encode(src, dst, win, box, dur, ff, crf):
    vf = (f"crop={box['w']}:{box['h']}:{box['x']}:{box['y']},"
          f"scale={TARGET_W}:{TARGET_H}:flags=lanczos")
    cmd = [ff, "-y", "-ss", f"{win['start_t']:.3f}", "-t", f"{dur:.3f}",
           "-i", src, "-vf", vf, "-c:v", "libx264", "-crf", str(crf),
           "-preset", "medium", "-pix_fmt", "yuv420p", "-an",
           "-movflags", "+faststart", str(dst)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode == 0, (p.stderr or "").strip().splitlines()[-1:] or [""]


def _relpath(p):
    # relpath raises across Windows drive letters; the absolute path is a fine
    # fallback and this is only ever a provenance column.
    try:
        return os.path.relpath(p)
    except ValueError:
        return os.path.abspath(p)


def process(path, out_dir, model, ff, args):
    stem = Path(path).stem
    rec = {"clip": stem, "src": _relpath(path)}
    dst = Path(out_dir) / f"{stem}.mp4"
    if dst.exists() and dst.stat().st_size > 0 and not args.overwrite:
        rec.update(accepted=1, reason="already present")
        return rec

    sc, err = scan(path, model, args.scan_fps)
    if err:
        rec.update(accepted=0, reason=err)
        return rec
    rec.update(src_w=sc["w"], src_h=sc["h"], src_fps=round(sc["fps"], 3),
               src_dur=round(sc["dur"], 2))
    if sc["dur"] < args.min_dur:
        rec.update(accepted=0, reason=f"source {sc['dur']:.2f}s < {args.min_dur}s")
        return rec

    win, err = pick_window(sc, args.min_dur, args.max_upscale, args.min_sharpness)
    if err:
        rec.update(accepted=0, reason=err)
        return rec
    if win["motion_raw"] < FROZEN_RAW:
        rec.update(accepted=0, reason=f"frozen {win['motion_raw']:.2f}")
        return rec

    box, err = crop_box(win, sc, args.max_upscale)
    if err:
        rec.update(accepted=0, reason=err)
        return rec

    dur = min(win["dur"], args.max_dur) if args.max_dur else win["dur"]
    ok, msg = encode(path, dst, win, box, dur, ff, args.crf)
    if not ok:
        rec.update(accepted=0, reason=f"encode failed: {msg[0][:120]}")
        return rec

    rec.update(accepted=1, reason="", w=TARGET_W, h=TARGET_H,
               fps=round(sc["fps"], 3), duration=round(dur, 2),
               window_start=round(win["start_t"], 2),
               face_frac=box["face_frac"], upscale=box["upscale"],
               crop_w=box["w"], crop_h=box["h"],
               face_subject_h=round(win["face_h"], 1),
               motion_raw=round(win["motion_raw"], 3),
               luma_mean=round(win["luma"], 2), contrast=round(win["contrast"], 2),
               sharpness=round(win["sharp"], 1))

    side = {
        "clip_id": stem, "source": "real", "model": "real",
        "width": TARGET_W, "height": TARGET_H, "fps": round(sc["fps"], 3),
        "duration_s": round(dur, 2),
        "conformance": {
            "source_resolution": [sc["w"], sc["h"]],
            "source_fps": round(sc["fps"], 3),
            "window_start_sec": round(win["start_t"], 2),
            "crop": box, "upscale": box["upscale"],
            "fps_resampled": False,
            "note": "fps left at source rate by P0 5.1; upscale recorded not corrected",
        },
        "provenance": {"ai_generated": False, "synthetic_identity": False,
                       "real_person_depicted": True,
                       "project": "FairDeep-Fake Bench",
                       "purpose": "deepfake detector fairness evaluation (research only)"},
        "demographic": None,     # filled by label_strata.py
        "qc": {"status": "filtered"},
    }
    (Path(out_dir) / f"{stem}.json").write_text(json.dumps(side, indent=1))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", required=True, help="dir or glob of source videos")
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--min-dur", type=float, default=MIN_DUR,
                    help="shortest clean run kept (s); clips are not trimmed to a fixed length")
    ap.add_argument("--max-dur", type=float, default=0.0,
                    help="cap output length (s); 0 keeps the whole clean run")
    ap.add_argument("--min-sharpness", type=float, default=MIN_SHARPNESS,
                    help="Laplacian-variance floor; 0 keeps blurry footage")
    ap.add_argument("--max-upscale", type=float, default=2.0,
                    help="1.0 forbids upscaling entirely")
    ap.add_argument("--scan-fps", type=float, default=SCAN_FPS)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    pat = a.videos if any(ch in a.videos for ch in "*?[") else os.path.join(a.videos, "*.mp4")
    paths = sorted(glob.glob(pat))
    if a.limit:
        paths = paths[:a.limit]
    if not paths:
        print(f"no videos matched {pat}", file=sys.stderr)
        return 1

    out_dir = Path(a.out_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = yunet_model(Path(__file__).parent / "models")
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ff = "ffmpeg"

    print(f"filtering {len(paths)} clips -> {out_dir}")
    recs = []
    for i, p in enumerate(paths, 1):
        recs.append(process(p, out_dir, model, ff, a))
        if i % 25 == 0 or i == len(paths):
            acc = sum(r.get("accepted", 0) for r in recs)
            print(f"  {i}/{len(paths)}  accepted {acc} ({100*acc/len(recs):.0f}%)", flush=True)

    keys = ["clip", "accepted", "reason", "src_w", "src_h", "src_fps", "src_dur",
            "w", "h", "fps", "duration", "window_start", "face_frac", "upscale", "crop_w",
            "crop_h", "face_subject_h", "motion_raw", "luma_mean", "contrast",
            "sharpness", "src"]
    report = a.report or (out_dir.parent / "qc_report_real.csv")
    with open(report, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            w.writerow(r)

    acc = sum(r.get("accepted", 0) for r in recs)
    print(f"\naccepted {acc}/{len(recs)}")
    from collections import Counter
    for reason, n in Counter(r["reason"] for r in recs
                             if not r.get("accepted")).most_common(10):
        print(f"  {n:5d}  {reason}")
    print(f"wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
