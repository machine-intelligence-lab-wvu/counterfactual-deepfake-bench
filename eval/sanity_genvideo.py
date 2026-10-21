#!/usr/bin/env python
"""Sanity check against published numbers: score a Real/ + Fake/<source>/ video set with one of our
adapters, as released (no view). Used for GenVideo-Val (the DeMamba authors' validation set) and
for a seeded AIGVDBench test sample (eval.fetch_aigvdb_sample).

  python -m eval.sanity_genvideo --detector d3 --root <GenVideo-Val> --out results/sanity/d3_genvideo \
      [--per-source 1000]

Layout: <root>/Real/*.mp4 (MSR-VTT) and <root>/Fake/<generator>/*.mp4. --per-source samples that many
videos per source with a fixed seed (D3's eval.py uses the first 1,000 rows of each csv).

Reported numbers (--reference genvideo, the default):
  d3       Zheng et al. (arXiv 2508.00701) Table 1, D3 row, AP (real as the positive class, score =
           the raw second-order std, as in their eval.py); mean AP 98.46, mean AUC 97.72 (Table 8).
  demamba  our checkpoint card (Ahsanz/DeMamba-GenVideo100K FULL_val_metrics.txt), full set, random
           8-frame window: accuracy 88.74, AUC 96.67, AP 96.28, real recall 0.8316, per-generator
           recall and AP (AP of each generator's fakes vs all reals, fake positive).
--reference aigvdb: V-PVP paper (arXiv 2607.15321) Table 1, per-generator AUC on the AIGVDBench
Open-Source test split, rows V-PVP and DeCoF (the latter is AIGVDBench's DeCoF checkpoint).
"""
import argparse
import glob
import json
import os
import time

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

from eval.common import git_commit, gpu_name, utc_now
from eval.detectors import registry

D3_AP = {"Crafter": 98.53, "Gen2": 99.39, "HotShot": 98.52, "Lavie": 97.22, "ModelScope": 97.12,
         "MoonValley": 99.52, "MorphStudio": 98.68, "Show_1": 99.18, "Sora": 99.91,
         "WildScrape": 96.49}
DEMAMBA_AP = {"Crafter": 93.47, "Gen2": 94.11, "HotShot": 73.16, "Lavie": 76.28, "ModelScope": 77.74,
              "MoonValley": 88.95, "MorphStudio": 81.50, "Show_1": 60.35, "Sora": 20.71,
              "WildScrape": 65.46}
DEMAMBA_RECALL = {"Crafter": 0.9964, "Gen2": 0.9978, "HotShot": 0.9643, "Lavie": 0.9200,
                  "ModelScope": 0.9786, "MoonValley": 1.0, "MorphStudio": 0.9857, "Show_1": 0.9043,
                  "Sora": 0.9107, "WildScrape": 0.8193}


_T1 = [("I2V_EasyAnimate", 94.18, 90.84), ("I2V_LTX", 94.05, 90.55), ("I2V_Pyramid-Flow", 94.68, 95.54),
       ("I2V_SEINE", 97.48, 97.33), ("I2V_SVD", 94.53, 98.98), ("I2V_VideoCrafter", 97.19, 63.10),
       ("T2V_AccVideo", 97.75, 88.25), ("T2V_AnimateDiff", 96.84, 89.24),
       ("T2V_Cogvideox1.5", 93.82, 98.16), ("T2V_EasyAnimate", 94.82, 91.87),
       ("T2V_HunyuanVideo", 95.90, 86.33), ("T2V_IPOC", 96.11, 99.33), ("T2V_LTX", 95.82, 97.61),
       ("T2V_Open-Sora", 99.69, 99.76), ("T2V_Pyramid-Flow", 96.40, 99.76),
       ("T2V_RepVideo", 90.17, 97.22), ("T2V_VideoCrafter", 99.02, 89.25), ("T2V_Wan2.1", 87.67, 83.53),
       ("V2V_Cogvideox1.5", 97.45, 97.40), ("V2V_LTX", 91.96, 89.86)]
AIGVDB_AUC = {"vpvp": {g: v for g, v, _ in _T1}, "decof": {g: d for g, _, d in _T1}}
AIGVDB_MEAN = {"vpvp": 95.28, "decof": 92.20}


def index(root, per_source, seed):
    rows = [{"path": p, "source": "real", "label": 0}
            for p in glob.glob(os.path.join(root, "Real", "**", "*.mp4"), recursive=True)]
    for g in sorted(os.listdir(os.path.join(root, "Fake"))):
        rows += [{"path": p, "source": g, "label": 1}
                 for p in glob.glob(os.path.join(root, "Fake", g, "**", "*.mp4"), recursive=True)]
    rows = [r for r in rows if not os.path.basename(r["path"]).startswith("._")]   # macOS forks
    if not rows:
        raise SystemExit(f"no videos under {root}/Real or {root}/Fake/<generator>")
    df = pd.DataFrame(rows).sort_values("path")
    if per_source:
        df = pd.concat([d.sample(n=min(per_source, len(d)), random_state=seed)
                        for _, d in df.groupby("source")])     # keeps `source` (pandas 3)
    return df.reset_index(drop=True)


class _DS(torch.utils.data.Dataset):
    def __init__(self, det, paths):
        self.det, self.paths = det, paths

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        try:
            return i, self.det.prepare(self.paths[i]), ""
        except Exception as e:
            return i, None, f"{type(e).__name__}: {e}"[:300]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", required=True, choices=["d3", "demamba", "decof", "vpvp"])
    ap.add_argument("--reference", default="genvideo", choices=["genvideo", "aigvdb"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-source", type=int, default=0, help="0 = every video")
    ap.add_argument("--seed", type=int, default=20261021)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--reuse", action="store_true", help="summarise an existing scores.csv")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    det = registry.get(a.detector)
    t0 = time.time()
    if a.reuse:
        df = pd.read_csv(os.path.join(a.out, "scores.csv"), keep_default_na=False,
                         na_values=[""]).assign(error=lambda d: d["error"].fillna(""))
        if "source" not in df:            # scores written before the pandas 3 fix
            df["source"] = [("real" if "/Real/" in p else p.split("/Fake/")[1].split("/")[0])
                            for p in df["path"]]
        summarise(a, det, df, t0)
        return
    df = index(a.root, a.per_source, a.seed)
    det.load(torch.device("cuda"))
    dl = torch.utils.data.DataLoader(_DS(det, df["path"].tolist()), batch_size=a.batch_size,
                                     num_workers=a.workers, collate_fn=lambda b: b)
    score, err = np.full(len(df), np.nan), [""] * len(df)
    for batch in dl:
        ok = [(i, x) for i, x, e in batch if x is not None]
        for i, _, e in batch:
            err[i] = e
        by_len = {}                       # D3 gives 8 or 16 frames by clip length
        for i, x in ok:
            by_len.setdefault(tuple(x.shape), []).append((i, x))
        for grp in by_len.values():
            s = det.score(torch.stack([x for _, x in grp])).numpy()
            for (i, _), v in zip(grp, s):
                score[i] = v
    df["score"], df["error"] = score, err
    df.to_csv(os.path.join(a.out, "scores.csv"), index=False)
    summarise(a, det, df, t0)


def summarise(a, det, df, t0):
    d = df[df["score"].notna()]
    real = d[d["label"] == 0]
    rows = []
    for g, f in d[d["label"] == 1].groupby("source"):
        y = np.r_[np.ones(len(f)), np.zeros(len(real))]
        s = np.r_[f["score"], real["score"]]
        r = {"source": g, "n_fake": len(f), "n_real": len(real), "auc": 100 * roc_auc_score(y, s),
             "ap_fake_pos": 100 * average_precision_score(y, s),
             "recall_at_thr": float((f["score"] >= det.default_threshold).mean())}
        if a.reference == "aigvdb":
            r["paper_auc"] = AIGVDB_AUC.get(a.detector, {}).get(g, np.nan)
        elif a.detector == "d3":
            # the authors' AP: real is the positive class, raw std is the score
            std = 1 / s - 1
            r["ap_real_pos_std"] = 100 * average_precision_score(1 - y, std)
            r["paper_ap"] = D3_AP.get(g, np.nan)
        if a.detector == "demamba" and a.reference == "genvideo":
            r["card_ap"] = DEMAMBA_AP.get(g, np.nan)
            r["card_recall"] = DEMAMBA_RECALL.get(g, np.nan)
        rows.append(r)
    t = pd.DataFrame(rows)
    y, s = d["label"].to_numpy(), d["score"].to_numpy()
    summ = {"detector": det.identity(), "n_scored": int(len(d)), "n_failed": int(df["score"].isna().sum()),
            "overall_auc": 100 * roc_auc_score(y, s), "overall_ap_fake_pos": 100 * average_precision_score(y, s),
            "accuracy_at_thr": 100 * float(((s >= det.default_threshold) == (y == 1)).mean()),
            "real_recall_at_thr": float((real["score"] < det.default_threshold).mean()),
            "mean_auc_per_source": float(t["auc"].mean()), "per_source": a.per_source,
            "seed": a.seed, "seconds": round(time.time() - t0), "gpu": gpu_name(),
            "git_commit": git_commit(), "created": utc_now()}
    if a.reference == "aigvdb":
        summ["reference"] = "V-PVP paper Table 1 (AIGVDBench Open-Source test split)"
        summ["paper_mean_auc"] = AIGVDB_MEAN.get(a.detector)
        summ["paper_mean_auc_same_sources"] = float(t["paper_auc"].mean())
    elif a.detector == "d3":
        summ["mean_ap_real_pos_std"] = float(t["ap_real_pos_std"].mean())
        summ["paper_mean_ap"], summ["paper_mean_auc"] = 98.46, 97.72
    if a.detector == "demamba" and a.reference == "genvideo":
        summ.update(card_accuracy=88.74, card_auc=96.67, card_ap=96.28, card_real_recall=0.8316)
    t.to_csv(os.path.join(a.out, "per_source.csv"), index=False)
    json.dump(summ, open(os.path.join(a.out, "summary.json"), "w"), indent=2, default=str)
    print(t.round(2).to_string(index=False))
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in summ.items()
                      if k not in ("detector",)}, indent=1))


if __name__ == "__main__":
    main()
