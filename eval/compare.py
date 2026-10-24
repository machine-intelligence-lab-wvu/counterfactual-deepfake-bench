#!/usr/bin/env python
"""Cross-detector / cross-view tables and figures from the latest snapshots.

  python -m eval.compare            # -> results/compare/<YYYYMMDD-HHMM>/

Reads results/snapshots/<detector>/<view>/latest for every detector and view that has one.
Never mixes snapshots silently: every row names the snapshot it came from.
"""
import glob
import json
import os

import numpy as np
import pandas as pd

from eval.common import RESULTS, stamp, utc_now
from eval.figures import GEN_COLOR, GEN_LABEL, GEN_ORDER, INK2, _save, _style


def latest_snapshots():
    out = []
    for p in sorted(glob.glob(os.path.join(RESULTS, "snapshots", "*", "*", "latest"))):
        meta = json.load(open(os.path.join(p, "snapshot_meta.json")))
        out.append((meta["detector"]["detector"], meta["view"], os.path.realpath(p), meta))
    return out


def main():
    snaps = latest_snapshots()
    if not snaps:
        raise SystemExit("no snapshots")
    rows, pend = [], []
    for det, view, path, meta in snaps:
        sb = pd.read_csv(os.path.join(path, "tables", "score_by_breakdown.csv"))
        dr = pd.read_csv(os.path.join(path, "tables", "provisional_detection_rate.csv"))
        gp = pd.read_csv(os.path.join(path, "tables", "subgroup_gap_score.csv"))
        cf = os.path.join(path, "tables", "cf_spread.csv")
        cf = pd.read_csv(cf).set_index("generator") if os.path.exists(cf) else pd.DataFrame()
        for gen in sb.loc[sb["factor"] == "overall", "generator"]:
            s = sb[(sb["factor"] == "overall") & (sb["generator"] == gen)].iloc[0]
            d = dr[(dr["factor"] == "overall") & (dr["generator"] == gen)].iloc[0]
            r = {"detector": det, "view": view, "snapshot": meta["snapshot"],
                 "view_hash": meta["view_hash"], "generator": gen, "n": int(s["n"]),
                 "mean_score": s["estimate"], "mean_ci_lo": s["ci_lo"], "mean_ci_hi": s["ci_hi"],
                 "det_rate_provisional": d["estimate"], "det_ci_lo": d["ci_lo"],
                 "det_ci_hi": d["ci_hi"], "threshold": meta["threshold"]}
            for attr in ["race", "gender", "age_band"]:
                g = gp[(gp["generator"] == gen) & (gp["attribute"] == attr)]
                r[f"gap_{attr}"] = float(g["gap"].iloc[0]) if len(g) else np.nan
            r["cf_spread"] = float(cf.loc[gen, "cf_spread"]) if gen in cf.index else np.nan
            rows.append(r)
        pend.append({"detector": det, "view": view, "pending": "AUC/AP/EER/TPR@5%FPR, real FPR, "
                     "calibrated threshold (needs reals)"})
    df = pd.DataFrame(rows)
    out = os.path.join(RESULTS, "compare", stamp())
    os.makedirs(os.path.join(out, "figures"), exist_ok=True)
    df.to_csv(os.path.join(out, "overall_by_generator.csv"), index=False, float_format="%.6g")
    pd.DataFrame(pend).to_csv(os.path.join(out, "pending.csv"), index=False)

    plt = _style()
    keys = [(d, v) for d, v, _, _ in snaps]
    figs = []
    for metric, lo, hi, label, name in [
            ("mean_score", "mean_ci_lo", "mean_ci_hi", "mean score", "mean_score_by_detector_view"),
            ("det_rate_provisional", "det_ci_lo", "det_ci_hi",
             "detection rate (provisional threshold)", "detection_rate_by_detector_view")]:
        fig, ax = plt.subplots(figsize=(8, 6))
        gens = [g for g in GEN_ORDER if g in set(df["generator"])]
        off = np.linspace(-0.25, 0.25, len(gens)) if len(gens) > 1 else [0]
        for k, g in enumerate(gens):
            dg = df[df["generator"] == g].set_index(["detector", "view"])
            y = np.arange(len(keys)) + off[k]
            est = [dg.loc[kk, metric] if kk in dg.index else np.nan for kk in keys]
            l = [dg.loc[kk, lo] if kk in dg.index else np.nan for kk in keys]
            h = [dg.loc[kk, hi] if kk in dg.index else np.nan for kk in keys]
            ax.hlines(y, l, h, color=GEN_COLOR[g], linewidth=2)
            ax.plot(est, y, "o", color=GEN_COLOR[g], markersize=6, markeredgecolor="white",
                    label=GEN_LABEL[g])
        ax.set_yticks(range(len(keys)), [f"{d} / {v}" for d, v in keys])
        ax.invert_yaxis()
        ax.set_xlim(0, 1)
        ax.set_xlabel(label)
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(gens))
        ax.set_title(f"{label} by detector and view, 95% CI", loc="left", pad=28)
        if "provisional" in label:
            fig.text(0.99, 0.005, "provisional threshold; replaced once reals exist",
                     ha="right", fontsize=8, color=INK2)
        _save(fig, os.path.join(out, "figures"), name, figs)
    with open(os.path.join(out, "README.md"), "w") as fh:
        fh.write(f"# Cross-detector comparison ({utc_now()})\n\nSnapshots: " +
                 ", ".join(f"{d}/{v} ({m['snapshot']})" for d, v, _, m in snaps) + "\n\n" +
                 df.drop(columns=["view_hash"]).round(4).to_markdown(index=False) + "\n\n" +
                 "".join(f"![{f}](figures/{f}.png)\n\n" for f in figs) +
                 "Pending until reals exist: " + pend[0]["pending"] + ".\n")
    print(out)


if __name__ == "__main__":
    main()
