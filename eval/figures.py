"""Snapshot figures (EVALUATION_PLAN.md section 7). PNG 300 dpi + PDF, 4:3.

Colour: generators use the first three slots of the reference categorical palette in fixed
order (ltx23 blue, wan22 orange, hunyuan15 aqua) so a generator keeps its colour in every
figure; magnitude uses one sequential blue ramp. Provisional-threshold figures carry a
"provisional threshold" label.
"""
import os

import numpy as np

GEN_ORDER = ["ltx23", "wan22", "hunyuan15"]
GEN_COLOR = {"ltx23": "#2a78d6", "wan22": "#eb6834", "hunyuan15": "#1baf7a"}
GEN_LABEL = {"ltx23": "LTX 2.3", "wan22": "Wan 2.2", "hunyuan15": "HunyuanVideo 1.5"}
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
PROV = "provisional threshold"


def _style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False,
        "savefig.bbox": "tight", "pdf.fonttype": 42})
    return plt


def _save(fig, fdir, name, out):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(fdir, f"{name}.{ext}"), dpi=300)
    import matplotlib.pyplot as plt
    plt.close(fig)
    out.append(name)


def _gens(df):
    return [g for g in GEN_ORDER if g in set(df["generator"])]


def _note(fig, text):
    fig.text(0.99, 0.005, text, ha="right", va="bottom", fontsize=8, color=MUTED)


def score_hist(fakes, fdir, out, title_sfx):
    plt = _style()
    gens = _gens(fakes)
    fig, axes = plt.subplots(len(gens), 1, figsize=(8, 6), sharex=True, squeeze=False)
    bins = np.linspace(0, 1, 41)
    for ax, g in zip(axes[:, 0], gens):
        s = fakes.loc[fakes["generator"] == g, "score"]
        ax.hist(s, bins=bins, color=GEN_COLOR[g], edgecolor="white", linewidth=0.8)
        ax.set_ylabel("clips")
        ax.text(0.01, 0.92, f"{GEN_LABEL[g]}  (n={len(s)}, mean {s.mean():.3f})",
                transform=ax.transAxes, va="top", color=INK)
    axes[-1, 0].set_xlabel("detector score (higher = more likely generated)")
    fig.suptitle(f"Score distribution by generator{title_sfx}", x=0.02, ha="left")
    _save(fig, fdir, "score_distribution_by_generator", out)


def cell_heatmap(table, fdir, out, name, title, cbar_label, note=None):
    plt = _style()
    from matplotlib.colors import LinearSegmentedColormap
    t = table[(table["factor"] == "cell") & (table["generator"].isin(GEN_ORDER))]
    gens = [g for g in GEN_ORDER if g in set(t["generator"])]
    cells = sorted(t["level"].unique())
    M = np.full((len(cells), len(gens)), np.nan)
    for j, g in enumerate(gens):
        tg = t[t["generator"] == g].set_index("level")["estimate"]
        M[:, j] = [tg.get(c, np.nan) for c in cells]
    fig, ax = plt.subplots(figsize=(6, 13))
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    im = ax.imshow(M, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(gens)), [GEN_LABEL[g] for g in gens])
    ax.set_yticks(range(len(cells)), [c.replace("__", " / ") for c in cells], fontsize=7)
    ax.grid(False)
    for i in range(len(cells)):
        for j in range(len(gens)):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6,
                        color="white" if M[i, j] > 0.55 else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.02)
    cb.set_label(cbar_label)
    ax.set_title(title, loc="left")
    if note:
        _note(fig, note)
    _save(fig, fdir, name, out)


def pointrange(table, factors, fdir, out, name, title, xlabel, note=None):
    """One panel per factor: level means with 95% CI, one marker per generator."""
    plt = _style()
    t = table[table["factor"].isin(factors) & table["generator"].isin(GEN_ORDER)]
    gens = [g for g in GEN_ORDER if g in set(t["generator"])]
    nrow = len(factors)
    heights = [max(1, t[t["factor"] == f]["level"].nunique()) for f in factors]
    fig, axes = plt.subplots(nrow, 1, figsize=(8, max(6, 0.32 * sum(heights) + 1.2 * nrow)),
                             gridspec_kw={"height_ratios": heights}, squeeze=False, sharex=True)
    off = np.linspace(-0.22, 0.22, len(gens)) if len(gens) > 1 else [0]
    for ax, f in zip(axes[:, 0], factors):
        tf = t[t["factor"] == f]
        levels = sorted(tf["level"].astype(str).unique())
        for k, g in enumerate(gens):
            tg = tf[tf["generator"] == g].assign(level=lambda d: d["level"].astype(str)).set_index("level")
            y = np.arange(len(levels)) + off[k]
            est = np.array([tg["estimate"].get(l, np.nan) for l in levels])
            lo = np.array([tg["ci_lo"].get(l, np.nan) for l in levels])
            hi = np.array([tg["ci_hi"].get(l, np.nan) for l in levels])
            ax.hlines(y, lo, hi, color=GEN_COLOR[g], linewidth=2)
            solo = np.isnan(lo) & ~np.isnan(est)      # level from one group: no interval
            ax.plot(est[~solo], y[~solo], "o", color=GEN_COLOR[g], markersize=5,
                    markeredgecolor="white", markeredgewidth=1, label=GEN_LABEL[g])
            ax.plot(est[solo], y[solo], "o", markerfacecolor="white", markeredgecolor=GEN_COLOR[g],
                    markersize=5, markeredgewidth=1.5)
        ax.set_yticks(range(len(levels)), levels)
        ax.invert_yaxis()
        ax.set_ylabel(f.replace("_", " "), color=INK)
    axes[0, 0].legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=len(gens))
    axes[0, 0].set_title(title, loc="left", pad=26)
    axes[-1, 0].set_xlabel(xlabel)
    _note(fig, ("hollow marker = level seen in one counterfactual group (no interval)"
                + (f"; {note}" if note else "")))
    _save(fig, fdir, name, out)


def per_generator_bar(table, value, fdir, out, name, title, xlabel, note=None):
    plt = _style()
    t = table.set_index("generator")
    gens = [g for g in GEN_ORDER if g in t.index]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    for i, g in enumerate(gens):
        ax.barh(i, t.loc[g, value], color=GEN_COLOR[g], height=0.6)
        ax.hlines(i, t.loc[g, "ci_lo"], t.loc[g, "ci_hi"], color=INK, linewidth=1.5)
        ax.text(t.loc[g, "ci_hi"] + 0.01, i, f"{t.loc[g, value]:.3f}  ({int(t.loc[g, 'n_groups'])} groups)",
                va="center", color=INK2, fontsize=9)
    ax.set_yticks(range(len(gens)), [GEN_LABEL[g] for g in gens])
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left")
    ax.grid(axis="y", visible=False)
    if note:
        _note(fig, note)
    _save(fig, fdir, name, out)


def cf_spread_hist(per_group, fdir, out):
    plt = _style()
    gens = [g for g in GEN_ORDER if g in set(per_group["generator"])]
    fig, ax = plt.subplots(figsize=(8, 6))
    bins = np.linspace(0, max(0.05, per_group["cf_spread"].max() * 1.05), 25)
    for g in gens:
        ax.hist(per_group.loc[per_group["generator"] == g, "cf_spread"], bins=bins,
                histtype="step", linewidth=2, color=GEN_COLOR[g], label=GEN_LABEL[g])
    ax.set_xlabel("CF spread: std of score across a group's cells")
    ax.set_ylabel("counterfactual groups")
    ax.legend()
    ax.set_title("Counterfactual consistency: per-group score spread", loc="left")
    _save(fig, fdir, "cf_spread_distribution", out)


def variance_share(anova, fdir, out):
    plt = _style()
    a = anova[anova["factor"] != "Residual"].sort_values("partial_eta2")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(a["factor"].str.replace("_", " "), a["partial_eta2"], color=SEQ[4], height=0.6)
    for i, (v, s) in enumerate(zip(a["partial_eta2"], a["ss_share"])):
        ax.text(v, i, f"  {v:.3f}  ({100 * s:.1f}% of total SS)", va="center", fontsize=9, color=INK2)
    ax.set_xlabel("partial eta squared (type II ANOVA, OLS)")
    ax.set_title("Factor attribution: variance in score by factor", loc="left")
    ax.grid(axis="y", visible=False)
    _save(fig, fdir, "factor_attribution_variance_share", out)


def example_strip(fakes, fdir, out, k=5):
    import av
    plt = _style()
    top = fakes.sort_values("score", ascending=False).head(k)
    bot = fakes.sort_values("score").head(k)
    fig, axes = plt.subplots(2, k, figsize=(12, 6.2))
    for r, (rows, lab) in enumerate([(top, "highest"), (bot, "lowest")]):
        for c, row in enumerate(rows.itertuples()):
            ax = axes[r, c]
            ax.axis("off")
            try:
                with av.open(row.out_path) as cont:
                    s = cont.streams.video[0]
                    frames = [f for _, f in zip(range(60), cont.decode(s))]
                    ax.imshow(frames[len(frames) // 2].to_ndarray(format="rgb24"))
            except Exception:
                ax.text(0.5, 0.5, "frame unavailable", ha="center")
            ax.set_title(f"{lab} #{c + 1}: {row.score:.3f}\n{GEN_LABEL.get(row.generator, row.generator)}\n"
                         f"{row.race}/{row.gender}/{row.age_band}\n{row.setting}, {row.lighting}",
                         fontsize=8, loc="left", color=INK)
    fig.suptitle("Highest- and lowest-scoring clips (middle frame of the view video)", x=0.02, ha="left")
    _save(fig, fdir, "example_strip", out)


def make_all(fakes, T, thr, fdir, det, view, spec):
    out = []
    sfx = f"  [{det.name}, {view}]"
    score_hist(fakes, fdir, out, sfx)
    cell_heatmap(T["score_by_breakdown"], fdir, out, "heatmap_mean_score_cells",
                 f"Mean score: 56 cells x generator{sfx}", "mean score")
    cell_heatmap(T["provisional_detection_rate"], fdir, out, "heatmap_detection_rate_cells_provisional",
                 f"Detection rate (score >= {thr}): 56 cells x generator", "detection rate",
                 note=f"{PROV} = {thr} (detector default); replaced once reals exist")
    pointrange(T["score_by_breakdown"], ["race", "gender", "age_band"], fdir, out,
               "subgroup_mean_score", f"Mean score by subgroup, 95% CI{sfx}", "mean score")
    pointrange(T["score_by_breakdown"], ["setting", "lighting", "behavior", "camera", "duration_nominal"],
               fdir, out, "scene_factor_mean_score", f"Mean score by scene factor, 95% CI{sfx}",
               "mean score")
    pointrange(T["provisional_detection_rate"], ["race", "gender", "age_band"], fdir, out,
               "subgroup_detection_rate_provisional",
               f"Detection rate by subgroup, 95% CI ({PROV} {thr})", "detection rate",
               note=f"{PROV} = {thr}")
    if not T["cf_spread_per_group"].empty:
        cf_spread_hist(T["cf_spread_per_group"], fdir, out)
    if not T["provisional_flip_rate"].empty:
        per_generator_bar(T["provisional_flip_rate"], "flip_rate", fdir, out,
                          "flip_rate_by_generator_provisional",
                          f"Flip rate by generator, 95% CI ({PROV} {thr})",
                          "share of counterfactual groups with mixed decisions",
                          note=f"{PROV} = {thr}")
    fa = T.get("factor_anova")
    if fa is not None and fa["partial_eta2"].notna().any():
        variance_share(fa, fdir, out)
    if "out_path" in fakes.columns:
        example_strip(fakes, fdir, out)
    return out
