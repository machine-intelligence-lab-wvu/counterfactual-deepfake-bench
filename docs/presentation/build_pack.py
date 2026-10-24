#!/usr/bin/env python3
"""Rebuild the presentation upload pack from the newest result snapshots.

Reads the `latest` symlink under each results/snapshots/<detector>/<view>/, so a
re-run after new scoring picks up the new snapshots with no edits. Run from the
repo root:  python docs/presentation/build_pack.py
"""
import csv, glob, json, os, shutil, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACK = os.path.join(REPO, "docs", "presentation")
TAB, FIG = os.path.join(PACK, "tables"), os.path.join(PACK, "figures")
os.chdir(REPO)
for d in (TAB, FIG):
    os.makedirs(d, exist_ok=True)

DEMOG = {"overall", "race", "gender", "age_band"}
SCENE = {"setting", "lighting", "behavior", "camera", "duration_nominal"}


def latest_snapshots():
    """[(detector, view, snapshot_dir)] for every detector/view with a `latest` link."""
    out = []
    for link in sorted(glob.glob("results/snapshots/*/*/latest")):
        parts = link.split(os.sep)
        det, view = parts[2], parts[3]
        if det == "generator":
            continue
        out.append((det, view, os.path.join(os.path.dirname(link), os.readlink(link))))
    return out


SRC = latest_snapshots()


def combine(table, outname, row_filter=None):
    rows, cols = [], None
    for det, view, d in SRC:
        p = os.path.join(d, "tables", f"{table}.csv")
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            if row_filter and not row_filter(r):
                continue
            if cols is None:
                cols = ["detector", "view"] + list(r.keys())
            rows.append({"detector": det, "view": view, **r})
    if not rows:
        print(f"  (skip {table})")
        return
    with open(os.path.join(TAB, f"{outname}.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"  {outname}.csv  {len(rows)} rows")


print(f"Detector snapshots: {len(SRC)}")
for det, view, d in SRC:
    print(f"  {det:9s} {view:13s} {os.path.basename(d)}")

print("\nDetector tables:")
combine("rf_auc",                     "01_realfake_auc_by_generator")
combine("rf_worst_subgroup_auc",      "02_worstgroup_auc_gaps")
combine("rf_subgroup_auc",            "03_subgroup_auc_full")
combine("rf_real_fpr",                "04_real_fpr_by_subgroup")
combine("rf_real_fpr_gap",            "05_real_fpr_gaps")
combine("provisional_detection_rate", "06_detection_rate_by_subgroup", lambda r: r["factor"] in DEMOG)
combine("provisional_detection_rate", "06b_detection_rate_scene_factors", lambda r: r["factor"] in SCENE)
combine("provisional_detection_rate", "06c_detection_rate_56cells", lambda r: r["factor"] == "cell")
combine("factor_anova",               "07_factor_attribution_anova")
combine("cf_spread",                  "08_counterfactual_spread")
combine("inclusion",                  "09_inclusion_coverage")
combine("sensitivity_inclusion_set",  "16_sensitivity_inclusion_set")

# ---- generator benchmark (FairFace fidelity, QC, quality proxies)
G = os.path.join("results/snapshots/generator",
                 os.readlink("results/snapshots/generator/latest"), "tables")
print("\nGenerator benchmark tables:")


def gen_combine(metrics, outname, prefix, factors=DEMOG):
    rows, cols = [], None
    for m in metrics:
        p = os.path.join(G, f"{prefix}_{m}.csv")
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p)):
            if factors and r.get("factor") not in factors:
                continue
            if cols is None:
                cols = ["metric"] + list(r.keys())
            rows.append({"metric": m, **r})
    with open(os.path.join(TAB, f"{outname}.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"  {outname}.csv  {len(rows)} rows")


gen_combine(["race_match", "gender_match", "age_match", "cell_match", "no_face"],
            "10_fairface_fidelity", "fidelity")
gen_combine(["qc_motion_norm", "face_sharpness", "qc_luma_mean", "qc_contrast"],
            "15_quality_proxies", "quality")
for src, dst, fac in [("confusion_race", "11_confusion_race", None),
                      ("confusion_age_band", "12_confusion_age_band", None),
                      ("fidelity_cell_match", "13_fidelity_by_56cells", {"cell"}),
                      ("qc_acceptance_primary", "14_qc_acceptance", DEMOG)]:
    rows = [r for r in csv.DictReader(open(os.path.join(G, f"{src}.csv")))
            if fac is None or r.get("factor") in fac]
    with open(os.path.join(TAB, f"{dst}.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"  {dst}.csv  {len(rows)} rows")

# ---- sanity checks: does each detector reproduce its own published benchmark?
print("\nSanity-check tables:")
summ, per = [], []
for d in sorted(glob.glob("results/sanity/*/")):
    name = os.path.basename(d.rstrip("/"))
    sp = os.path.join(d, "summary.json")
    if os.path.exists(sp):
        s = json.load(open(sp))
        det = (s.get("detector") or {}).get("detector", name.split("_")[0])
        summ.append({
            "check": name, "detector": det,
            "benchmark": "GenVideo-Val" if "genvideo" in name else "AIGVDBench",
            "n_scored": s.get("n_scored"), "n_failed": s.get("n_failed"),
            "our_auc": s.get("overall_auc"), "our_mean_auc_per_source": s.get("mean_auc_per_source"),
            "our_ap": s.get("overall_ap_fake_pos"), "our_accuracy": s.get("accuracy_at_thr"),
            "paper_auc": s.get("paper_mean_auc") or s.get("card_auc"),
            "paper_ap": s.get("paper_mean_ap") or s.get("card_ap"),
            "paper_accuracy": s.get("card_accuracy"),
            "checkpoint_sha256": (s.get("detector") or {}).get("checkpoint_sha256"),
            "gpu": s.get("gpu"), "created": s.get("created"),
        })
    pp = os.path.join(d, "per_source.csv")
    if os.path.exists(pp):
        for r in csv.DictReader(open(pp)):
            if per == [] :
                cols_per = ["check", "detector"] + list(r.keys())
            per.append({"check": name,
                        "detector": name.split("_")[0], **r})
if summ:
    with open(os.path.join(TAB, "17_sanity_reference_benchmarks.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys())); w.writeheader(); w.writerows(summ)
    print(f"  17_sanity_reference_benchmarks.csv  {len(summ)} rows")
if per:
    keys = []
    for r in per:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(TAB, "18_sanity_per_source.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader(); w.writerows(per)
    print(f"  18_sanity_per_source.csv  {len(per)} rows")

# ---- figures, from the newest snapshot of each detector
print("\nFigures:")
by = {(d, v): p for d, v, p in SRC}
WANT = [
    ("compare", None, "detection_rate_by_detector_view.png", "01_detection_rate_by_detector_view.png"),
    ("compare", None, "mean_score_by_detector_view.png",     "02_mean_score_by_detector_view.png"),
    ("demamba", "native_up_2s", "subgroup_auc.png",          "03_subgroup_auc_demamba.png"),
    ("demamba", "native_up_2s", "roc_per_generator.png",     "04_roc_per_generator_demamba.png"),
    ("decof",   "native_up_2s", "subgroup_auc.png",          "05_subgroup_auc_decof.png"),
    ("decof",   "native_up_2s", "roc_per_generator.png",     "06_roc_per_generator_decof.png"),
    ("decof",   "native_up_2s", "factor_attribution_variance_share.png", "07_factor_attribution_decof.png"),
    ("demamba", "native_up_2s", "real_fpr_by_subgroup.png",  "08_real_fpr_by_subgroup_demamba.png"),
    ("demamba", "native_up_2s", "heatmap_detection_rate_cells_provisional.png", "09_heatmap_56cells_demamba.png"),
    ("demamba", "native_up_2s", "score_distribution_by_generator.png", "10_score_distribution_demamba.png"),
]
cmp_dir = sorted(glob.glob("results/compare/2026*"))[-1]
for det, view, src, dst in WANT:
    base = cmp_dir if det == "compare" else by.get((det, view))
    if base is None:
        print(f"  (missing {det}/{view})"); continue
    p = os.path.join(base, "figures", src)
    if os.path.exists(p):
        shutil.copy(p, os.path.join(FIG, dst)); print(f"  {dst}")
    else:
        print(f"  (missing {p})")
# generator benchmark figures
GF = os.path.join(os.path.dirname(G), "figures")
for src, dst in [("fidelity_race_match.png", "11_fairface_race_fidelity.png"),
                 ("confusion_race.png", "12_confusion_race.png"),
                 ("heatmap_cell_fidelity.png", "13_heatmap_cell_fidelity.png")]:
    p = os.path.join(GF, src)
    if os.path.exists(p):
        shutil.copy(p, os.path.join(FIG, dst)); print(f"  {dst}")

# ---- narrative documents
print("\nNarrative:")
shutil.copy("eval/LOG.md", os.path.join(PACK, "METHODS_LOG.md")); print("  METHODS_LOG.md")
shutil.copy(os.path.join(cmp_dir, "README.md"),
            os.path.join(PACK, "CROSS_DETECTOR_SUMMARY.md")); print("  CROSS_DETECTOR_SUMMARY.md")
parts = ["# Filtered vs unfiltered reals — every view\n",
         "Concatenated from `results/compare/real_all/`. The real-half filter's verdict is kept\n"
         "per clip, so the same scores are read both ways.\n"]
for f in sorted(glob.glob("results/compare/real_all/*.md")):
    parts.append(f"\n<!-- {os.path.basename(f)} -->\n" + open(f).read())
open(os.path.join(PACK, "REAL_ALL_FILTERED_VS_UNFILTERED.md"), "w").write("\n".join(parts))
print("  REAL_ALL_FILTERED_VS_UNFILTERED.md")
print("\nDone. 00_START_HERE.md and GENERATION_OVERVIEW.md are maintained by hand.")
