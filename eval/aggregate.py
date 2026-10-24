#!/usr/bin/env python
"""Aggregate every scored batch for one detector and view into a timestamped snapshot.

  python -m eval.aggregate --detector decof --view face512 [--set primary] [--B 1000]

Unions the scores of all active batches (eval/manifests/eval_sets.yaml), joins manifests,
refuses to mix detector identities or view hashes, computes every section-6 metric the data
supports and marks the rest `pending`. Output:

  results/snapshots/<detector>/<view>/<YYYYMMDD-HHMM>/
      manifest_used.csv  scores.csv  tables/*.csv  figures/*.{png,pdf}  REPORT.md  snapshot_meta.json
  results/snapshots/<detector>/<view>/latest -> <newest>
"""
import argparse
import json
import os
import re
import socket
import warnings

import numpy as np
import pandas as pd

from eval.common import REPO, RESULTS, batch_info, eval_sets, git_commit, stamp, utc_now
from eval.detectors import registry
from eval.metrics import (B_DEFAULT, SEED, GroupBootstrap, cf_spread_per_group, ci,
                          detection_rate, flip_per_group, gap, gap_reps, summary)
from eval.preprocess import latest_records
from eval.run import read_scores
from eval.views.spec import load as load_view

DEMO = ["race", "gender", "age_band", "cell"]
SCENE = ["setting", "lighting", "behavior", "camera", "duration_nominal"]
GEN_ORDER = ["ltx23", "wan22", "hunyuan15", "ltx25"]
PENDING_63 = [
    ("AUC, AP, EER, TPR@5%FPR (overall, per generator)", "needs reals (real_b1)"),
    ("Calibrated threshold (5% FPR on fps-matched reals)", "needs reals (real_b1)"),
    ("Real FPR by perceived race, gender, age band, race x gender", "needs reals (real_b1)"),
    ("Detection rate and flip rate at the calibrated threshold", "needs reals (real_b1)"),
    ("Worst-subgroup AUC, subgroup AUC gap", "needs reals (real_b1)"),
    ("ROC curves per generator; real FPR by subgroup (figures)", "needs reals (real_b1)"),
]


# ------------------------------------------------------------------------------ inputs
def load_scores(det, view, vh, batches, allow_other=False):
    parts = [read_scores(det.name, view, b) for b in batches]
    rows = pd.concat([p for p in parts if not p.empty], ignore_index=True) if any(
        not p.empty for p in parts) else pd.DataFrame()
    if rows.empty:
        raise SystemExit(f"no scores for {det.name}/{view} in batches {batches}")
    match = ((rows["checkpoint_sha256"] == det.checkpoint_sha256)
             & (rows["view_hash"] == vh) & (rows["detector_version"] == det.version))
    other = rows[~match]
    if len(other) and not allow_other:
        ids = other[["detector_version", "checkpoint_sha256", "view_hash"]].drop_duplicates()
        raise SystemExit("refusing to mix detector/view identities; found rows from:\n"
                         f"{ids.to_string(index=False)}\ncurrent: {det.version} "
                         f"{det.checkpoint_sha256} {vh}\n(--allow-other-identities ignores them)")
    last = rows[match].sort_values("timestamp").groupby("clip_id", as_index=False).tail(1)
    return last[last["status"] == "ok"].copy(), last[last["status"] != "ok"].copy(), int(len(other))


def manifests(batches):
    out = []
    for b in batches:
        info = batch_info(b)
        m = pd.read_csv(os.path.join(REPO, info["manifest"]), dtype={"clip_id": str})
        m["kind"] = info["kind"]
        out.append(m)
    return pd.concat(out, ignore_index=True)


def source_id(clip_id):
    return re.sub(r"__fps\d+$", "", clip_id)


# ------------------------------------------------------------------------------ tables
def breakdown_table(df, gb, value, B_rates=False):
    """Mean (or rate) + CI for overall and every factor, per generator and pooled."""
    rows = []
    gens = [g for g in GEN_ORDER if g in set(df["generator"])] + sorted(
        set(df["generator"]) - set(GEN_ORDER))
    for gen in gens + ["all"]:
        d = df if gen == "all" else df[df["generator"] == gen]
        for factor in ["overall"] + DEMO + SCENE:
            levels = [("all", d)] if factor == "overall" else sorted(
                d.groupby(factor), key=lambda t: str(t[0]))
            for lev, dd in levels:
                pt, reps = gb.mean(dd[value], dd["counterfactual_group"])
                # resampling whole groups cannot express uncertainty for a level seen in a
                # single group (every replicate is the same mean or missing): no interval
                lo, hi = ci(reps) if dd["counterfactual_group"].nunique() >= 2 else (np.nan, np.nan)
                r = {"generator": gen, "factor": factor, "level": lev, "n": len(dd),
                     "n_groups": dd["counterfactual_group"].nunique(), "estimate": pt,
                     "ci_lo": lo, "ci_hi": hi}
                if value == "score":
                    s = summary(dd["score"])
                    r.update({k: s[k] for k in ["sd", "median", "q05", "q25", "q75", "q95"]})
                rows.append(r)
    return pd.DataFrame(rows)


def gap_table(df, gb, value):
    rows = []
    gens = [g for g in GEN_ORDER if g in set(df["generator"])]
    for gen in gens + ["all"]:
        d = df if gen == "all" else df[df["generator"] == gen]
        for factor in DEMO + SCENE:
            levs, means, reps = [], [], []
            for lev, dd in d.groupby(factor):
                pt, rp = gb.mean(dd[value], dd["counterfactual_group"])
                levs.append(lev); means.append(pt); reps.append(rp)
            if len(levs) < 2:
                continue
            lo, hi = ci(gap_reps(np.vstack(reps)))
            i_max, i_min = int(np.nanargmax(means)), int(np.nanargmin(means))
            rows.append({"generator": gen, "attribute": factor, "n_levels": len(levs),
                         "gap": gap(means), "ci_lo": lo, "ci_hi": hi,
                         "max_level": levs[i_max], "max_mean": means[i_max],
                         "min_level": levs[i_min], "min_mean": means[i_min]})
    return pd.DataFrame(rows)


def per_group_table(df, gb, fn, name):
    rows, per = [], []
    for gen in [g for g in GEN_ORDER if g in set(df["generator"])]:
        d = df[df["generator"] == gen]
        s = fn(d)
        if s.empty:
            continue
        pt, reps = gb.group_mean(s.to_numpy(), s.index.to_numpy())
        lo, hi = ci(reps)
        rows.append({"generator": gen, "n_groups": len(s), name: pt, "ci_lo": lo, "ci_hi": hi,
                     "median": float(s.median()), "max": float(s.max())})
        per.append(pd.DataFrame({"generator": gen, "counterfactual_group": s.index,
                                 name: s.to_numpy()}))
    return pd.DataFrame(rows), (pd.concat(per, ignore_index=True) if per else pd.DataFrame())


def factor_attribution(df):
    """OLS type-II ANOVA (partial eta^2, SS share), lighting x race test, and the mixed model."""
    import statsmodels.formula.api as smf
    from statsmodels.stats.anova import anova_lm
    terms = [f for f in ["race", "gender", "age_band"] + SCENE + ["generator"]
             if df[f].nunique() > 1]
    rhs = " + ".join(f"C({t})" for t in terms)
    d = df.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ols = smf.ols(f"score ~ {rhs}", data=d).fit()
        an = anova_lm(ols, typ=2)
        ss_res = an.loc["Residual", "sum_sq"]
        ss_tot = float(((d["score"] - d["score"].mean()) ** 2).sum())
        an = an.rename(index=lambda s: s.replace("C(", "").replace(")", ""))
        an["partial_eta2"] = an["sum_sq"] / (an["sum_sq"] + ss_res)
        an["ss_share"] = an["sum_sq"] / ss_tot
        an.loc["Residual", ["partial_eta2"]] = np.nan
        an = an.reset_index().rename(columns={"index": "factor", "PR(>F)": "p"})
        inter = None
        if {"lighting", "race"} <= set(terms):
            o2 = smf.ols(f"score ~ {rhs} + C(lighting):C(race)", data=d).fit()
            a2 = anova_lm(o2, typ=2)
            k = "C(lighting):C(race)"
            inter = pd.DataFrame([{"term": "lighting x race", "df": a2.loc[k, "df"],
                                   "sum_sq": a2.loc[k, "sum_sq"], "F": a2.loc[k, "F"],
                                   "p": a2.loc[k, "PR(>F)"],
                                   "partial_eta2": a2.loc[k, "sum_sq"] /
                                   (a2.loc[k, "sum_sq"] + a2.loc["Residual", "sum_sq"])}])
        mixed, var = None, None
        try:
            mm = smf.mixedlm(f"score ~ {rhs}", data=d, groups=d["counterfactual_group"]).fit(
                reml=True, method="lbfgs")
            mixed = pd.DataFrame({"term": mm.fe_params.index, "coef": mm.fe_params.values,
                                  "se": mm.bse_fe.values, "p": mm.pvalues[mm.fe_params.index].values})
            g_var, r_var = float(mm.cov_re.iloc[0, 0]), float(mm.scale)
            var = pd.DataFrame([{"component": "counterfactual_group (random intercept)",
                                 "variance": g_var}, {"component": "residual", "variance": r_var},
                                {"component": "ICC (group share of random variance)",
                                 "variance": g_var / (g_var + r_var)}])
            var["converged"] = bool(mm.converged)
        except Exception as e:
            var = pd.DataFrame([{"component": "mixed model failed", "variance": np.nan,
                                 "converged": False, "error": str(e)[:200]}])
    return an, inter, mixed, var, terms


# ------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--set", default="primary", choices=["primary", "all"])
    ap.add_argument("--B", type=int, default=B_DEFAULT)
    ap.add_argument("--threshold", type=float, default=None,
                    help="override the provisional threshold (default: detector's official)")
    ap.add_argument("--allow-other-identities", action="store_true")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--out-root", default=os.path.join(RESULTS, "snapshots"))
    a = ap.parse_args()

    det = registry.get(a.detector)
    spec = load_view(a.view, check_toolchain=False)
    vh = spec["view_hash"]
    sets = eval_sets()
    batches = [b for b in sets["active"]]
    ok, failed, n_other = load_scores(det, a.view, vh, batches, a.allow_other_identities)
    man = manifests(batches)

    ok["source_clip_id"] = ok["clip_id"].map(source_id)
    df_all = ok.merge(man.rename(columns={"clip_id": "source_clip_id", "batch": "m_batch"}),
                      on="source_clip_id", how="left", validate="many_to_one")
    if df_all["generator"].isna().any() & (df_all["kind"] == "fake").any():
        missing = df_all[df_all["generator"].isna()]["clip_id"].head().tolist()
        raise SystemExit(f"scored clips missing from manifests: {missing}")
    fakes_all = df_all[df_all["kind"] == "fake"].copy()
    reals = df_all[df_all["kind"] == "real"].copy()
    fakes = fakes_all[fakes_all["primary"] == 1].copy() if a.set == "primary" else fakes_all
    thr = det.default_threshold if a.threshold is None else a.threshold

    snap = os.path.join(a.out_root, det.name, a.view, stamp())
    tdir, fdir = os.path.join(snap, "tables"), os.path.join(snap, "figures")
    os.makedirs(tdir, exist_ok=True); os.makedirs(fdir, exist_ok=True)
    T = {}

    # inclusion / coverage
    render = pd.concat([latest_records(a.view, b, vh).assign(batch=b) for b in batches
                        if not latest_records(a.view, b, vh).empty], ignore_index=True)
    used = man[["clip_id", "batch", "kind", "generator", "primary"]].copy()
    # reals have one render per fps; a source counts as rendered only if all renders are ok
    rs = (render.groupby("source_clip_id")["status"].agg(
        lambda st: "ok" if (st == "ok").all() else ("failed" if (st == "failed").any()
                                                      else st.iloc[0]))
          if not render.empty else pd.Series(dtype=str))
    used["render_status"] = used["clip_id"].map(rs).fillna("pending")
    sc = ok.groupby("source_clip_id")["score"].mean()
    used["scored"] = used["clip_id"].isin(sc.index).astype(int)
    used["score_failed"] = used["clip_id"].isin(failed["clip_id"].map(source_id)).astype(int)
    used["included"] = (used["scored"] & ((used["primary"] == 1) if a.set == "primary"
                                          else True)).astype(int)
    used.to_csv(os.path.join(snap, "manifest_used.csv"), index=False)
    inc = used.groupby(["batch", "generator"]).agg(
        clips=("clip_id", "size"), primary=("primary", "sum"),
        rendered=("render_status", lambda s: int((s == "ok").sum())),
        view_excluded=("render_status", lambda s: int((s == "excluded").sum())),
        render_failed=("render_status", lambda s: int((s == "failed").sum())),
        scored=("scored", "sum"), score_failed=("score_failed", "sum"),
        included=("included", "sum")).reset_index()
    T["inclusion"] = inc
    df_all[["clip_id", "batch", "generator", "cell", "counterfactual_group", "primary",
            "score", "timestamp"]].sort_values("clip_id").to_csv(
        os.path.join(snap, "scores.csv"), index=False, float_format="%.6f")
    if a.view.startswith("face512") and not render.empty:
        r_ok = render[render["status"] == "ok"]
        T["window_shift"] = pd.DataFrame([{
            "rendered": len(r_ok), "shifted_long_axis": int(r_ok["shifted_x"].sum()),
            "shifted_short_axis": int(r_ok["shifted_y"].sum()),
            "max_shift_long_px": int(r_ok["shift_x_px"].max()) if len(r_ok) else 0,
            "excluded_no_face": int(render["error"].str.startswith("no face").sum())}])

    # 6.1
    gb = GroupBootstrap(fakes_all["counterfactual_group"], B=a.B, seed=SEED)
    T["score_by_breakdown"] = breakdown_table(fakes, gb, "score")
    T["subgroup_gap_score"] = gap_table(fakes, gb, "score")
    T["cf_spread"], T["cf_spread_per_group"] = per_group_table(
        fakes, gb, cf_spread_per_group, "cf_spread")
    try:
        an, inter, mixed, var, terms = factor_attribution(fakes)
    except Exception as e:      # e.g. too few clips for the number of factor levels
        an = pd.DataFrame([{"factor": "not estimable", "df": np.nan, "sum_sq": np.nan,
                            "F": np.nan, "p": np.nan, "partial_eta2": np.nan, "ss_share": np.nan,
                            "reason": f"{type(e).__name__}: {e}"[:300]}])
        inter, mixed, terms = None, None, []
        var = pd.DataFrame([{"component": "not estimable", "variance": np.nan,
                             "converged": False, "reason": an.loc[0, "reason"]}])
    T["factor_anova"], T["factor_mixed_fixed"], T["factor_mixed_variance"] = an, mixed, var
    if inter is not None:
        T["factor_lighting_x_race"] = inter
    # 6.2 provisional
    fakes["detected"] = (fakes["score"] >= thr).astype(float)
    T["provisional_detection_rate"] = breakdown_table(fakes, gb, "detected")
    T["provisional_detection_gap"] = gap_table(fakes, gb, "detected")
    T["provisional_flip_rate"], T["provisional_flip_per_group"] = per_group_table(
        fakes, gb, lambda d: flip_per_group(d, thr), "flip_rate")
    # sensitivity: all scored fakes
    s_all = []
    for gen, d in fakes_all.groupby("generator"):
        s_all.append({"set": "all", "generator": gen, "n": len(d), "mean_score": d["score"].mean(),
                      "provisional_detection_rate": detection_rate(d["score"], thr)})
    for gen, d in fakes.groupby("generator"):
        s_all.append({"set": a.set, "generator": gen, "n": len(d), "mean_score": d["score"].mean(),
                      "provisional_detection_rate": detection_rate(d["score"], thr)})
    T["sensitivity_inclusion_set"] = pd.DataFrame(s_all)
    # 6.3
    reals_p = reals[reals["primary"] == 1].copy() if a.set == "primary" else reals
    rf, roc = None, {}
    if len(reals_p):
        from eval.realfake import RealFake
        rf = RealFake(fakes, reals_p, gb, B=a.B)
        T["rf_threshold"] = rf.threshold_table()
        T["rf_auc"] = rf.auc_table()
        T["rf_real_fpr"], T["rf_real_fpr_gap"] = rf.real_fpr_table()
        T["rf_subgroup_auc"], T["rf_worst_subgroup_auc"] = rf.subgroup_auc_tables()
        fakes["detected_cal"] = (fakes["score"] >= rf.thr).astype(float)
        T["calibrated_detection_rate"] = breakdown_table(fakes, gb, "detected_cal")
        T["calibrated_detection_gap"] = gap_table(fakes, gb, "detected_cal")
        T["calibrated_flip_rate"], T["calibrated_flip_per_group"] = per_group_table(
            fakes, gb, lambda d: flip_per_group(d, rf.thr), "flip_rate")
        roc = rf.roc_points()
    else:
        T["pending_metrics"] = pd.DataFrame([{"metric": m, "status": "pending", "reason": r}
                                             for m, r in PENDING_63])
    for k, v in T.items():
        if v is not None and not v.empty:
            v.to_csv(os.path.join(tdir, f"{k}.csv"), index=False, float_format="%.6g")

    if not render.empty:
        fakes = fakes.merge(render[["clip_id", "out_path"]], on="clip_id", how="left")
    figs = []
    if not a.no_figures:
        from eval import figures
        figs = figures.make_all(fakes, T, thr, fdir, det, a.view, spec)
        if rf is not None:
            figs += figures.make_realfake(T, roc, rf.thr, fdir, det, a.view)

    meta = {"detector": det.identity(), "threshold": thr, "threshold_source":
            det.threshold_source if a.threshold is None else "override", "provisional": True,
            "calibrated_threshold": rf.thr if rf is not None else None,
            "calibration": ("score at which 5% of primary real renders (24 and 16 fps pooled) "
                            "are flagged" if rf is not None else "pending (no reals)"),
            "n_included_reals": int(len(reals_p)),
            "view": a.view, "view_hash": vh, "ffmpeg": spec["toolchain"]["ffmpeg_version"],
            "batches": batches, "inclusion_set": a.set, "bootstrap": {"B": a.B, "seed": SEED,
            "unit": "counterfactual_group"}, "n_scored": int(len(ok)), "n_failed": int(len(failed)),
            "n_included_fakes": int(len(fakes)), "n_reals": int(len(reals)),
            "ignored_other_identity_rows": n_other, "factor_terms": terms,
            "git_commit": git_commit(), "created": utc_now(), "snapshot": os.path.basename(snap),
            "host": socket.gethostname()}
    with open(os.path.join(snap, "snapshot_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, default=str)
    from eval.report import write_report
    write_report(snap, meta, T, figs, det, spec)
    latest = os.path.join(os.path.dirname(snap), "latest")
    tmp = latest + ".tmp"
    if os.path.lexists(tmp):
        os.remove(tmp)
    os.symlink(os.path.basename(snap), tmp)
    os.replace(tmp, latest)
    try:
        from eval.coverage import write_coverage
        write_coverage()
    except Exception as e:
        print(f"coverage not updated: {e}")
    print(f"snapshot {snap}\n  fakes included {len(fakes)}, real renders included {len(reals_p)}"
          f" / scored {len(ok)}; "
          f"{len(T)} tables, {len(figs)} figures")


if __name__ == "__main__":
    main()
