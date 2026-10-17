#!/usr/bin/env python
"""Technical QC scan over generated clips (plan section 7.1 / 7.3 subset).

Covers the checks that need no ML models, so it runs immediately after
generation, before FairFace / MiVOLO / ArcFace are wired in:
  - container conformance: resolution, fps, frame count, audio track
  - temporal sanity: frozen clips, black frames, stalled frames
  - framing artifacts: pillarboxing / letterboxing
  - with --faces: face count via YuNet (qc/faces.py), for the "exactly one
    face" gate. Reported as its own verdict, `face_pass`, separate from the
    technical `pass`, so either can be applied alone in analysis.

Expected resolution, fps, frame count and audio come from each clip's sidecar
(model-specific: LTX 2.3 is 24 fps with audio, Wan 2.2 is 16 fps without), with
the LTX values as fallback for clips that have no sidecar.

Motion is reported two ways. `motion_raw` is mean absolute inter-frame pixel
difference; it is luminance-dependent, so it under-reports movement on darker
faces and in dim scenes - which would manufacture a demographic bias out of a
metric artifact. `motion_norm` divides by frame contrast (std), giving a
brightness-independent figure. Compare both before concluding anything about
motion differing across demographic cells.

Writes qc_report.csv (per clip) and cell_summary.csv (per cell).
"""
import argparse, csv, glob, json, os
from concurrent.futures import ProcessPoolExecutor
import warnings
warnings.filterwarnings("ignore")

EXPECT_W, EXPECT_H, EXPECT_FPS = 1280, 704, 24.0
# Motion uses the first MAX_FRAMES frames. Inter-frame diffs are per frame, so at
# 16 fps (Wan) each diff spans 1.5x the time it does at 24 fps (LTX): compare
# motion within a generator, not across generators.
MAX_FRAMES = 40
FROZEN_RAW = 0.30
BLACK_MEAN = 8.0


def scan_one(path, faces=False):
    import av, numpy as np
    rec = {"path": os.path.relpath(path), "clip": os.path.basename(path)}
    exp = {"w": EXPECT_W, "h": EXPECT_H, "fps": EXPECT_FPS, "audio": True}
    side = os.path.splitext(path)[0] + ".json"
    if os.path.exists(side):
        s = json.load(open(side))
        d = s["demographic"]
        exp = {"w": s["width"], "h": s["height"], "fps": float(s["fps"]),
               "audio": s.get("generation", {}).get("audio", s["model"] == "ltx23")}
        rec.update(model=s["model"], cell=s["cell"], race=d["race"], gender=d["gender"],
                   age_band=d["age_band"], group=s["counterfactual_group"],
                   lighting=s["scene"]["lighting_key"],
                   setting=s["scene"]["setting_key"],
                   behavior=s["action"]["key"],
                   exp_len=s["length"], exp_dur=s["duration_s"])
    try:
        c = av.open(path)
        vs = c.streams.video[0]
        rec["w"], rec["h"] = vs.width, vs.height
        rec["fps"] = round(float(vs.average_rate), 3)
        rec["codec"] = vs.codec_context.name
        rec["audio"] = int(any(st.type == "audio" for st in c.streams))
        rec["n_frames_hdr"] = vs.frames or 0
        fr = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
        if faces and fr:
            from faces import analyse
            rec.update(analyse(fr))
        fr = fr[:MAX_FRAMES]
        if len(fr) < 2:
            rec["error"] = "fewer than 2 decodable frames"
            rec["pass"] = 0
            return rec
        a = np.stack(fr).astype(np.float32)
        diffs = np.abs(a[1:] - a[:-1]).mean(axis=(1, 2, 3))
        means = a.mean(axis=(1, 2, 3))
        stds = a.std(axis=(1, 2, 3))
        rec["motion_raw"] = round(float(diffs.mean()), 3)
        rec["motion_min"] = round(float(diffs.min()), 3)
        rec["motion_norm"] = round(float((diffs / (stds[:-1] + 1e-6)).mean()), 4)
        rec["luma_mean"] = round(float(means.mean()), 2)
        rec["contrast"] = round(float(stds.mean()), 2)
        rec["black_frames"] = int((means < BLACK_MEAN).sum())
        rec["stalled_frames"] = int((diffs < 0.02).sum())
        mid = a[len(a) // 2].mean(axis=2)
        col = mid.mean(axis=0)
        row = mid.mean(axis=1)
        rec["edge_l"] = round(float(col[:40].mean()), 2)
        rec["edge_r"] = round(float(col[-40:].mean()), 2)
        rec["edge_t"] = round(float(row[:30].mean()), 2)
        rec["edge_b"] = round(float(row[-30:].mean()), 2)
        centre = float(col[200:-200].mean())
        rec["pillarboxed"] = int(rec["edge_l"] < 12 and rec["edge_r"] < 12
                                 and centre > 25)
        rec["letterboxed"] = int(rec["edge_t"] < 12 and rec["edge_b"] < 12
                                 and centre > 25)
        fails = []
        if (rec["w"], rec["h"]) != (exp["w"], exp["h"]):
            fails.append(f"resolution {rec['w']}x{rec['h']}")
        if abs(rec["fps"] - exp["fps"]) > 0.01:
            fails.append(f"fps {rec['fps']}")
        if rec.get("exp_len") and rec["n_frames_hdr"] and \
                rec["n_frames_hdr"] != rec["exp_len"]:
            fails.append(f"frames {rec['n_frames_hdr']} != {rec['exp_len']}")
        if exp["audio"] and not rec["audio"]:
            fails.append("no audio track")
        if not exp["audio"] and rec["audio"]:
            fails.append("unexpected audio track")
        if rec["motion_raw"] < FROZEN_RAW:
            fails.append(f"frozen {rec['motion_raw']}")
        if rec["black_frames"]:
            fails.append(f"{rec['black_frames']} black frames")
        if rec["pillarboxed"]:
            fails.append("pillarboxed")
        if rec["letterboxed"]:
            fails.append("letterboxed")
        rec["fail_reasons"] = "; ".join(fails)
        rec["pass"] = int(not fails)
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:160]
        rec["pass"] = 0
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--tag", default="", help="suffix: qc_report_<tag>.csv")
    ap.add_argument("--faces", action="store_true", help="add YuNet face-count columns")
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.root, "**", "*.mp4"), recursive=True))
    print(f"scanning {len(paths)} clips with {a.workers} workers ...", flush=True)
    recs = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, r in enumerate(ex.map(scan_one, paths, [a.faces] * len(paths),
                                     chunksize=8), 1):
            recs.append(r)
            if i % 25 == 0 or i == len(paths):
                print(f"  {i}/{len(paths)}", flush=True)

    os.makedirs(a.out_dir, exist_ok=True)
    keys = ["clip", "model", "cell", "race", "gender", "age_band", "group", "lighting",
            "setting", "behavior", "w", "h", "fps", "codec", "audio",
            "n_frames_hdr", "exp_len", "exp_dur", "motion_raw", "motion_min",
            "motion_norm", "luma_mean", "contrast", "black_frames",
            "stalled_frames", "edge_l", "edge_r", "edge_t", "edge_b",
            "pillarboxed", "letterboxed"]
    if a.faces:
        keys += ["face_frames", "face_none_frames", "face_bg_frames",
                 "face_bg_max_count", "face_secondary_rel_max", "face_subject_h",
                 "face_subject_cx", "face_bg_people", "face_pass"]
    keys += ["pass", "fail_reasons", "error", "path"]
    sfx = f"_{a.tag}" if a.tag else ""
    qc = os.path.join(a.out_dir, f"qc_report{sfx}.csv")
    with open(qc, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            w.writerow(r)

    if a.faces:
        fp = [r for r in recs if r.get("face_pass")]
        both = [r for r in fp if r.get("pass")]
        print(f"face_pass {len(fp)}/{len(recs)}  "
              f"(background people {sum(r.get('face_bg_people', 0) for r in recs)})  "
              f"technical+face {len(both)}/{len(recs)}")
    ok = [r for r in recs if r.get("pass")]
    bad = [r for r in recs if not r.get("pass")]
    print(f"\npass {len(ok)}/{len(recs)}  fail {len(bad)}")
    from collections import Counter, defaultdict
    if bad:
        print("  failure reasons:")
        for reason, n in Counter(r.get("fail_reasons") or r.get("error", "?")
                                 for r in bad).most_common(10):
            print(f"    {n:5d}  {reason}")

    import statistics as st
    per = defaultdict(list)
    for r in recs:
        if "cell" in r:
            per[r["cell"]].append(r)
    cs = os.path.join(a.out_dir, f"cell_summary{sfx}.csv")
    with open(cs, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "race", "gender", "age_band", "n", "n_pass",
                    "pass_rate", "motion_raw_mean", "motion_norm_mean",
                    "luma_mean", "n_frozen", "n_pillarboxed"])
        for cell in sorted(per):
            rs = per[cell]
            g = [r for r in rs if "motion_raw" in r]
            race, gender, age = cell.split("__")
            w.writerow([cell, race, gender, age, len(rs),
                        sum(r.get("pass", 0) for r in rs),
                        round(sum(r.get("pass", 0) for r in rs) / len(rs), 4),
                        round(st.mean([r["motion_raw"] for r in g]), 3) if g else "",
                        round(st.mean([r["motion_norm"] for r in g]), 4) if g else "",
                        round(st.mean([r["luma_mean"] for r in g]), 2) if g else "",
                        sum(1 for r in g if r["motion_raw"] < FROZEN_RAW),
                        sum(r.get("pillarboxed", 0) for r in g)])
    print(f"\nwrote {qc}\nwrote {cs}")


if __name__ == "__main__":
    main()
