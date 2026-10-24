#!/usr/bin/env python
"""Build a fake-batch manifest from a combined fairdeep-bench metadata.csv.

One row per clip: every metadata column, plus
  clip_id       prompt_id (unique across generators)
  batch, label  batch name, 1 (generated)
  path          absolute path of the source .mp4
  generator     model key (ltx23, wan22, hunyuan15, ltx25)
  duration_nominal  5 or 6 (requested clip length; views trim to 5.0 s)
  qc_technical  technical QC pass (0/1)
  qc_face       face QC pass (0/1)
  primary       qc_technical AND qc_face

  python -m eval.manifests.build_fake_manifest --batch fake_b1 \
      --data-root /work/nvme/bjej/rahamed/fairdeep/eval/fairdeep-bench
"""
import argparse
import os

import pandas as pd

from eval.common import MANIFEST_DIR

REQUIRED = ["clip_id", "batch", "label", "path", "generator", "cell", "race", "gender",
            "age_band", "counterfactual_group", "setting", "lighting", "behavior", "camera",
            "duration_nominal", "width", "height", "fps", "duration_s", "seed",
            "qc_technical", "qc_face", "primary"]


def build(data_root, batch):
    md = pd.read_csv(os.path.join(data_root, "metadata.csv"), dtype=str, keep_default_na=False)
    df = md.copy()
    df.insert(0, "clip_id", md["prompt_id"])
    df.insert(1, "batch", batch)
    df.insert(2, "label", 1)
    df.insert(3, "path", [os.path.join(data_root, f) for f in md["file_name"]])
    df["generator"] = md["model"]
    df["duration_nominal"] = md["duration_s"].astype(float).round().astype(int)
    for c in ["width", "height", "fps", "counterfactual_group"]:
        df[c] = df[c].astype(int)
    df["duration_s"] = df["duration_s"].astype(float)
    df["qc_technical"] = (md["qc_pass"] == "1").astype(int)
    df["qc_face"] = (md["qc_face_pass"] == "1").astype(int)
    df["primary"] = (df["qc_technical"] & df["qc_face"]).astype(int)
    return df.sort_values("clip_id").reset_index(drop=True)


def validate(df):
    """Schema checks shared with the tests. Raises ValueError on the first problem."""
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    if df["clip_id"].duplicated().any():
        raise ValueError("duplicate clip_id")
    for c in ["qc_technical", "qc_face", "primary", "label"]:
        if not set(df[c].unique()) <= {0, 1}:
            raise ValueError(f"{c} must be 0/1")
    if ((df["qc_technical"] & df["qc_face"]) != df["primary"]).any():
        raise ValueError("primary must equal qc_technical AND qc_face")
    if df[["cell", "race", "gender", "age_band", "generator"]].eq("").any().any():
        raise ValueError("empty demographic or generator field")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--check-files", action="store_true", help="stat every path")
    a = ap.parse_args()
    df = build(a.data_root, a.batch)
    validate(df)
    if a.check_files:
        bad = [p for p in df["path"] if not os.path.isfile(p)]
        if bad:
            raise SystemExit(f"{len(bad)} missing files, first: {bad[0]}")
    out = os.path.join(MANIFEST_DIR, f"{a.batch}.csv")
    df.to_csv(out, index=False)
    print(f"{out}: {len(df)} clips, primary {int(df['primary'].sum())}, "
          f"by generator {df.groupby('generator').size().to_dict()}")


if __name__ == "__main__":
    main()
