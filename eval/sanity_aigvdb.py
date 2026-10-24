#!/usr/bin/env python
"""Sanity check: score AIGVDBench test videos with our DeCoF adapter, compare with the paper.

  python -m eval.sanity_aigvdb --manifest $FAIRDEEP_EXT/aigvdb_sanity/sanity_manifest.csv \
      --out results/sanity/decof_aigvdb

Videos are scored as released (already H.264), with no view applied: this checks the adapter
against the authors' protocol, not our views. Reported AUCs are AIGVDBench (arXiv 2601.11035)
Table 3, T2V rows of the DeCoF line.
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score

from eval.common import git_commit, gpu_name, utc_now
from eval.detectors import registry

PAPER_AUC = {"opensora": 99.90, "ltx": 87.74, "hunyuan": 79.82, "wan21": 72.90}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    man = pd.read_csv(a.manifest)
    det = registry.get("decof")
    det.load(torch.device("cuda"))
    t0, scores, errs = time.time(), [], []
    for p in man["path"]:
        try:
            scores.append(float(det.score(det.prepare(p).unsqueeze(0))[0])); errs.append("")
        except Exception as e:
            scores.append(np.nan); errs.append(f"{type(e).__name__}: {e}")
    dt = time.time() - t0
    man["score"], man["error"] = scores, errs
    man["pred_fake"] = (man["score"] >= det.default_threshold).astype(int)
    real = man[man["source"] == "real"]
    rows = [{"source": "real", "n": len(real), "mean_score": real["score"].mean(),
             "acc_at_0.5": float((real["pred_fake"] == 0).mean()), "auc_vs_real": np.nan,
             "paper_auc": np.nan}]
    for src, d in man[man["source"] != "real"].groupby("source"):
        y = np.r_[np.zeros(len(real)), np.ones(len(d))]
        s = np.r_[real["score"], d["score"]]
        rows.append({"source": src, "n": len(d), "mean_score": d["score"].mean(),
                     "acc_at_0.5": float((d["pred_fake"] == 1).mean()),
                     "auc_vs_real": 100 * roc_auc_score(y, s), "paper_auc": PAPER_AUC.get(src)})
    res = pd.DataFrame(rows)
    os.makedirs(a.out, exist_ok=True)
    man.drop(columns=["path"]).to_csv(os.path.join(a.out, "scores.csv"), index=False)
    res.to_csv(os.path.join(a.out, "summary.csv"), index=False)
    meta = {**det.identity(), "n": len(man), "failed": int(man["score"].isna().sum()),
            "seconds": round(dt, 1), "gpu": gpu_name(), "git_commit": git_commit(),
            "created": utc_now(), "manifest": a.manifest}
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), indent=2)
    print(res.to_string(index=False))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
