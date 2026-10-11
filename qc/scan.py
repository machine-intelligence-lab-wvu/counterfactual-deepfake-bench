#!/usr/bin/env python
"""Technical QC scan over generated clips (plan section 7.1 / 7.3 subset).

Covers the checks that need no ML models, so it runs immediately after
generation, before FairFace / MiVOLO / ArcFace are wired in:
  - container conformance: resolution, fps, frame count, audio track
  - temporal sanity: frozen clips, black frames, stalled frames
  - framing artifacts: pillarboxing / letterboxing

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
MAX_FRAMES = 40
FROZEN_RAW = 0.30
BLACK_MEAN = 8.0


def scan_one(path):
    import av, numpy as np
    rec = {"path": os.path.relpath(path), "clip": os.path.basename(path)}
    side = os.path.splitext(path)[0] + ".json"
    if os.path.exists(side):
        s = json.load(open(side))
        d = s["demographic"]
        rec.update(cell=s["cell"], race=d["race"], gender=d["gender"],
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
        fr = []
        for i, f in enumerate(c.decode(video=0)):
            fr.append(f.to_ndarray(format="rgb24"))
            if i + 1 >= MAX_FRAMES:
                break
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
        if (rec["w"], rec["h"]) != (EXPECT_W, EXPECT_H):
            fails.append(f"resolution {rec['w']}x{rec['h']}")
        if abs(rec["fps"] - EXPECT_FPS) > 0.01:
            fails.append(f"fps {rec['fps']}")
        if rec.get("exp_len") and rec["n_frames_hdr"] and \
                rec["n_frames_hdr"] != rec["exp_len"]:
            fails.append(f"frames {rec['n_frames_hdr']} != {rec['exp_len']}")
        if not rec["audio"]:
            fails.append("no audio track")
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
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.root, "**", "*.mp4"), recursive=True))
    print(f"scanning {len(paths)} clips with {a.workers} workers ...", flush=True)
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        recs = list(ex.map(scan_one, paths, chunksize=8))

    os.makedirs(a.out_dir, exist_ok=True)
    keys = ["clip", "cell", "race", "gender", "age_band", "group", "lighting",
            "setting", "behavior", "w", "h", "fps", "codec", "audio",
            "n_frames_hdr", "exp_len", "exp_dur", "motion_raw", "motion_min",
            "motion_norm", "luma_mean", "contrast", "black_frames",
            "stalled_frames", "edge_l", "edge_r", "edge_t", "edge_b",
            "pillarboxed", "letterboxed", "pass", "fail_reasons", "error", "path"]
    qc = os.path.join(a.out_dir, "qc_report.csv")
    with open(qc, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            w.writerow(r)

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
    cs = os.path.join(a.out_dir, "cell_summary.csv")
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
