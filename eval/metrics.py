"""Metric functions (EVALUATION_PLAN.md section 6). Pure numpy/pandas, unit-tested.

Uncertainty: 95% percentile intervals from B bootstrap resamples with a fixed seed. Fakes are
resampled by whole counterfactual group; a group id names the same scene (setting, lighting,
behavior, camera) in every generator, so one resample of group ids is shared by every
breakdown, generator and statistic - gaps and rates computed from the same resample are
mutually consistent.

All per-resample statistics are computed from per-group sums, so a resample is a matrix
product: W (B x G, how often each group was drawn) @ per-group sums.
"""
import numpy as np
import pandas as pd

B_DEFAULT = 1000
SEED = 20261020


class GroupBootstrap:
    """Shared cluster bootstrap over counterfactual groups."""

    def __init__(self, group_ids, B=B_DEFAULT, seed=SEED):
        self.groups = np.array(sorted(pd.unique(np.asarray(group_ids))))
        self.index = {g: i for i, g in enumerate(self.groups)}
        G = len(self.groups)
        rng = np.random.default_rng(seed)
        draws = rng.integers(0, G, size=(B, G))
        self.W = np.zeros((B, G))
        for b in range(B):
            self.W[b] = np.bincount(draws[b], minlength=G)
        self.B = B

    def gidx(self, group_ids):
        return np.array([self.index[g] for g in np.asarray(group_ids)])

    def sums(self, values, group_ids):
        gi = self.gidx(group_ids)
        G = len(self.groups)
        S = np.bincount(gi, weights=np.asarray(values, float), minlength=G)
        N = np.bincount(gi, minlength=G).astype(float)
        return S, N

    def mean(self, values, group_ids):
        """Point mean and its bootstrap replicates (B,) for clip-level values."""
        values = np.asarray(values, float)
        if len(values) == 0:
            return np.nan, np.full(self.B, np.nan)
        S, N = self.sums(values, group_ids)
        with np.errstate(invalid="ignore", divide="ignore"):
            reps = (self.W @ S) / (self.W @ N)
        return float(values.mean()), reps

    def group_mean(self, per_group_values, group_ids):
        """Mean of one value per group (e.g. CF spread, flip indicator) and replicates."""
        return self.mean(per_group_values, group_ids)


def ci(reps, alpha=0.05):
    r = np.asarray(reps, float)
    r = r[~np.isnan(r)]
    if len(r) == 0:
        return np.nan, np.nan
    return float(np.quantile(r, alpha / 2)), float(np.quantile(r, 1 - alpha / 2))


def gap(level_means):
    """Subgroup gap: max - min of the level means (NaN levels ignored)."""
    v = np.asarray(list(level_means), float)
    v = v[~np.isnan(v)]
    return float(v.max() - v.min()) if len(v) >= 2 else np.nan


def gap_reps(level_reps):
    """Replicates of the gap from a (levels x B) array of level-mean replicates."""
    a = np.asarray(level_reps, float)
    with np.errstate(invalid="ignore"):
        out = np.nanmax(a, axis=0) - np.nanmin(a, axis=0)
    n_ok = (~np.isnan(a)).sum(axis=0)
    out[n_ok < 2] = np.nan
    return out


def cf_spread_per_group(df, value="score", group="counterfactual_group"):
    """Std (ddof=0) of `value` across a group's clips (its cells); groups with < 2 clips dropped."""
    g = df.groupby(group)[value].agg(lambda s: float(np.std(s.to_numpy(), ddof=0))
                                     if len(s) >= 2 else np.nan)
    return g.dropna()


def flip_per_group(df, threshold, value="score", group="counterfactual_group"):
    """1 if a group's clips get different decisions at `threshold`, else 0 (>= 2 clips)."""
    def f(s):
        if len(s) < 2:
            return np.nan
        d = s.to_numpy() >= threshold
        return float(d.min() != d.max())
    return df.groupby(group)[value].agg(f).dropna()


def detection_rate(scores, threshold):
    s = np.asarray(scores, float)
    return float((s >= threshold).mean()) if len(s) else np.nan


def summary(values):
    v = np.asarray(values, float)
    if len(v) == 0:
        return {k: np.nan for k in ["n", "mean", "sd", "median", "q05", "q25", "q75", "q95"]}
    q = np.quantile(v, [0.05, 0.25, 0.5, 0.75, 0.95])
    return {"n": int(len(v)), "mean": float(v.mean()), "sd": float(v.std(ddof=1)) if len(v) > 1 else 0.0,
            "median": float(q[2]), "q05": float(q[0]), "q25": float(q[1]),
            "q75": float(q[3]), "q95": float(q[4])}
