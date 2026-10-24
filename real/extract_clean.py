#!/usr/bin/env python
"""Cut each accepted real clip's clean run out of its raw CelebV-HQ segment, losslessly, at
source resolution and fps.

filter_real.py conforms reals to the generation spec (crop + scale to 1280x704), which is the
right input for QC and labelling but not for detector evaluation: the eval views forbid
upscaling, and an upscale + second lossy encode is itself a cue a detector can separate the
halves on. The eval therefore reads these extracts and applies its own face window. Same clean
run (window_start, duration) that filter_real.py chose; x264 -qp 0 (lossless), no crop, no
scale, no fps change, no audio.

  python real/extract_clean.py --clips ../fairdeep-bench/real --raw ../celebvhq_raw \
      --out-root ../celebvhq_clean --workers 12
"""
import argparse, glob, json, os, subprocess, sys
from functools import partial
from multiprocessing import Pool


def extract(job, out_root, ff):
    clip, src, start, dur = job
    dst = os.path.join(out_root, clip + ".mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return clip, "skip", ""
    tmp = dst + ".tmp.mp4"
    cmd = [ff, "-v", "error", "-y", "-i", src, "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
           "-map", "0:v:0", "-c:v", "libx264", "-qp", "0", "-preset", "veryfast",
           "-an", "-map_metadata", "-1", tmp]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return clip, "fail", (p.stderr or "").strip()[-300:]
    os.replace(tmp, dst)
    return clip, "ok", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", required=True, help="filter_real.py output (sidecars)")
    ap.add_argument("--raw", required=True, help="raw CelebV-HQ segments (fetch_celebvhq.py)")
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--ffmpeg", default=os.environ.get("FAIRDEEP_FFMPEG", "ffmpeg"))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    jobs = []
    for sc in sorted(glob.glob(os.path.join(a.clips, "*.json"))):
        d = json.load(open(sc))
        if not os.path.exists(sc[:-5] + ".mp4"):
            continue
        jobs.append((d["clip_id"], os.path.join(a.raw, d["clip_id"] + ".mp4"),
                     float(d["conformance"]["window_start_sec"]), float(d["duration_s"])))
    os.makedirs(a.out_root, exist_ok=True)
    work = partial(extract, out_root=a.out_root, ff=a.ffmpeg)
    n = {"ok": 0, "skip": 0, "fail": 0}
    with Pool(a.workers) as pool:
        for i, (clip, st, err) in enumerate(pool.imap_unordered(work, jobs), 1):
            n[st] += 1
            if err:
                print(f"  {clip}: {err}", file=sys.stderr)
            if i % 200 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  {n}", flush=True)
    return 1 if n["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
