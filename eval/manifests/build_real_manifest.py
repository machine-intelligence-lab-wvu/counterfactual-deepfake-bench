#!/usr/bin/env python
"""Build a real-batch manifest (real_b1) from the real-half outputs.

Inputs (counterfactual-deepfake-bench branch real-half):
  --clips   filter_real.py output: one sidecar per accepted clip, with the FairFace labels
            written by label_strata.py --stage label
  --clean   extract_clean.py output: each clip's clean run cut losslessly from the raw
            CelebV-HQ segment at source resolution and fps. These are the files the views
            read, so the eval applies its own face window and never sees an upscaled copy.
  --info    celebvhq_info.json (YouTube id per clip, used as the identity cluster)

One row per clip, columns as in real_b1.template.csv plus:
  race, gender, age_band   = the perceived labels, under the fake manifest's column names
  race_conf, gender_conf, age_conf, age_ambiguous, age_band_alt, cell
  label_confidence         min of the three FairFace confidences
  identity_cluster         YouTube video id: clips cut from one video share a person, so
                           real-side CIs resample videos, not clips
  primary                  passed the real-set face gate AND labelled into a taxonomy cell
                           (FairFace 0-19 is never in a cell; see real/fairface.py)

  python -m eval.manifests.build_real_manifest --batch real_b1 --clips <real dir> \
      --clean <celebvhq_clean> --info <celebvhq_info.json>
"""
import argparse
import glob
import json
import os
import subprocess

import pandas as pd

from eval.common import FFPROBE, MANIFEST_DIR


def probe(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate,nb_frames:format=duration",
                          "-of", "json", path], capture_output=True, text=True, check=True)
    j = json.loads(out.stdout)
    s, f = j["streams"][0], j["format"]
    num, den = (int(x) for x in s["avg_frame_rate"].split("/"))
    return int(s["width"]), int(s["height"]), round(num / den, 3), float(f["duration"])


def build(batch, clips, clean, info):
    ytb = {k: v["ytb_id"] for k, v in json.load(open(info))["clips"].items()}
    rows = []
    for sc in sorted(glob.glob(os.path.join(clips, "*.json"))):
        d = json.load(open(sc))
        cid = d["clip_id"]
        src = os.path.join(os.path.abspath(clean), cid + ".mp4")
        if not os.path.exists(src):
            continue
        dm = d.get("demographic") or {}
        labelled = bool(dm.get("ok")) and bool(dm.get("cell"))
        w, h, fps, dur = probe(src)
        confs = [dm.get("fairface_race_conf"), dm.get("fairface_gender_conf"),
                 dm.get("fairface_age_conf")]
        rows.append({
            "clip_id": f"celebvhq__{cid}", "batch": batch, "label": 0, "source_id": cid,
            "path": src,
            "perceived_race": dm.get("race", ""), "perceived_gender": dm.get("gender", ""),
            "perceived_age_band": dm.get("age_band", ""),
            "label_confidence": min(c for c in confs if c is not None) if labelled else "",
            "width": w, "height": h, "fps": fps, "duration_s": round(dur, 3),
            "face_gate": 1, "primary": int(labelled),
            "identity_cluster": ytb.get(cid, cid), "generator": "real",
            "race": dm.get("race", ""), "gender": dm.get("gender", ""),
            "age_band": dm.get("age_band", ""), "cell": dm.get("cell") or "",
            "race_conf": confs[0], "gender_conf": confs[1], "age_conf": confs[2],
            "age_ambiguous": dm.get("age_ambiguous", ""),
            "age_band_alt": dm.get("age_band_alt") or "",
            "cell_excluded_reason": dm.get("cell_excluded_reason") or "",
            "upscale_in_conformed_copy": d["conformance"]["upscale"],
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default="real_b1")
    ap.add_argument("--clips", required=True)
    ap.add_argument("--clean", required=True)
    ap.add_argument("--info", required=True)
    a = ap.parse_args()
    df = build(a.batch, a.clips, a.clean, a.info)
    out = os.path.join(MANIFEST_DIR, f"{a.batch}.csv")
    df.to_csv(out, index=False)
    print(f"{out}: {len(df)} clips, primary {int(df['primary'].sum())}, "
          f">= 5 s {int((df['duration_s'] >= 5.0 - 1e-3).sum())}, "
          f">= 2 s {int((df['duration_s'] >= 2.0 - 1e-3).sum())}, "
          f"videos {df['identity_cluster'].nunique()}")


if __name__ == "__main__":
    main()
