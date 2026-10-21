"""Section 6.3: metrics that need reals (EVALUATION_PLAN.md).

Threshold: one global threshold per detector and view, the score at which 5% of real renders
are flagged (score >= t), pooling the 24 and 16 fps renders of every primary real clip. Never
per subgroup.

Pairing: each generator's fakes are compared with the reals rendered at that generator's fps
(LTX/Hunyuan 24, Wan 16). "all" pools every fake with every real render.

Uncertainty: two-sample bootstrap. Fakes resample whole counterfactual groups (the shared
GroupBootstrap of aggregate.py, so these intervals use the same resamples as sections 6.1/6.2);
reals resample identity clusters (one per source YouTube video; per clip when absent). AUC
replicates use the weighted Mann-Whitney statistic, so a resample is a matrix product. AP and
EER are reported as point estimates.
"""
import numpy as np
import pandas as pd

from eval.metrics import B_DEFAULT, SEED, GroupBootstrap, ci, gap

FPR_TARGET = 0.05
MIN_REAL = 30          # fewer real renders than this in a subgroup -> AUC not estimable
GEN_FPS = {"ltx23": 24, "wan22": 16, "hunyuan15": 24}
ATTRS = ["race", "gender", "age_band", "race_gender"]


def calibrated_threshold(real_scores, fpr=FPR_TARGET):
    return float(np.quantile(np.asarray(real_scores, float), 1 - fpr))


def _pairs(f, r):
    f = np.asarray(f, np.float32)[:, None]
    r = np.asarray(r, np.float32)[None, :]
    return (f > r).astype(np.float32) + 0.5 * (f == r).astype(np.float32)


def auc_reps(f, r, wf, wr):
    """AUC (P(fake score > real score), ties 1/2) and B replicates from clip weights
    wf (B x n_fake) and wr (B x n_real)."""
    if len(f) == 0 or len(r) == 0:
        return np.nan, np.full(wf.shape[0], np.nan)
    M = _pairs(f, r)
    point = float(M.mean())
    MR = M @ wr.T.astype(np.float32)                    # n_fake x B
    num = (wf * MR.T).sum(1)
    den = wf.sum(1) * wr.sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return point, num / den


def ap_eer(f, r):
    from sklearn.metrics import average_precision_score, roc_curve
    y = np.r_[np.ones(len(f)), np.zeros(len(r))]
    s = np.r_[f, r]
    fpr, tpr, _ = roc_curve(y, s)
    i = int(np.nanargmin(np.abs(fpr - (1 - tpr))))
    return float(average_precision_score(y, s)), float((fpr[i] + 1 - tpr[i]) / 2)


def tpr_at_fpr(f, r, fpr=FPR_TARGET):
    t = calibrated_threshold(r, fpr)
    return float((np.asarray(f) >= t).mean()), t


class RealFake:
    def __init__(self, fakes, reals, gb_fake, B=B_DEFAULT):
        self.f = fakes.reset_index(drop=True)
        r = reals.reset_index(drop=True).copy()
        for k in ["race", "gender", "age_band"]:          # real manifests: perceived_* labels
            if f"perceived_{k}" in r:
                r[k] = r[k].where(r[k].notna(), r[f"perceived_{k}"]) if k in r else r[f"perceived_{k}"]
            r[k] = r[k].fillna("").astype(str)
        r["render_fps"] = r["clip_id"].str.extract(r"__fps(\d+)$")[0].astype(float)
        ic = r["identity_cluster"] if "identity_cluster" in r else pd.Series(np.nan, index=r.index)
        r["identity"] = ic.where(ic.notna() & (ic.astype(str) != ""), r["source_clip_id"]).astype(str)
        r["race_gender"] = np.where((r["race"] != "") & (r["gender"] != ""),
                                    r["race"] + "__" + r["gender"], "")     # unlabelled reals: no level
        self.r = r
        for k in ["race", "gender", "age_band"]:
            self.f[k] = self.f[k].fillna("").astype(str)
        self.f["race_gender"] = np.where((self.f["race"] != "") & (self.f["gender"] != ""),
                                         self.f["race"] + "__" + self.f["gender"], "")
        self.gb_f = gb_fake
        self.gb_r = GroupBootstrap(r["identity"], B=B, seed=SEED + 1)
        self.Wf = gb_fake.W[:, gb_fake.gidx(self.f["counterfactual_group"])]
        self.Wr = self.gb_r.W[:, self.gb_r.gidx(r["identity"])]
        self.thr = calibrated_threshold(r["score"])

    def _sel(self, gen, f_mask=None, r_mask=None):
        fm = np.ones(len(self.f), bool) if gen == "all" else (self.f["generator"] == gen).to_numpy()
        rm = np.ones(len(self.r), bool) if gen == "all" else (
            self.r["render_fps"] == GEN_FPS.get(gen, -1)).to_numpy()
        if f_mask is not None:
            fm = fm & f_mask           # not in place: pandas 3 hands out read-only arrays
        if r_mask is not None:
            rm = rm & r_mask
        return fm, rm

    def gens(self):
        g = [x for x in GEN_FPS if x in set(self.f["generator"])]
        return g + sorted(set(self.f["generator"]) - set(GEN_FPS)) + ["all"]

    # ------------------------------------------------------------------ tables
    def threshold_table(self):
        rows = [{"scope": "all real renders", "n_renders": len(self.r),
                 "n_sources": self.r["source_clip_id"].nunique(),
                 "n_identities": self.r["identity"].nunique(), "threshold": self.thr,
                 "fpr": float((self.r["score"] >= self.thr).mean())}]
        for fps, d in self.r.groupby("render_fps"):
            rows.append({"scope": f"{int(fps)} fps renders", "n_renders": len(d),
                         "n_sources": d["source_clip_id"].nunique(),
                         "n_identities": d["identity"].nunique(), "threshold": self.thr,
                         "fpr": float((d["score"] >= self.thr).mean())})
        return pd.DataFrame(rows)

    def auc_table(self):
        rows = []
        for gen in self.gens():
            fm, rm = self._sel(gen)
            f, r = self.f["score"].to_numpy()[fm], self.r["score"].to_numpy()[rm]
            auc, reps = auc_reps(f, r, self.Wf[:, fm], self.Wr[:, rm])
            lo, hi = ci(reps)
            ap, eer = ap_eer(f, r)
            tpr5, t5 = tpr_at_fpr(f, r)
            det = (f >= self.thr).astype(float)
            dpt, dreps = self.gb_f.mean(det, self.f["counterfactual_group"].to_numpy()[fm])
            dlo, dhi = ci(dreps)
            rows.append({"generator": gen, "real_fps": "24+16" if gen == "all" else GEN_FPS.get(gen),
                         "n_fake": int(fm.sum()), "n_real": int(rm.sum()),
                         "auc": auc, "auc_ci_lo": lo, "auc_ci_hi": hi, "ap": ap, "eer": eer,
                         "tpr_at_5fpr": tpr5, "threshold_5fpr_pair": t5,
                         "detection_rate_global_thr": dpt, "det_ci_lo": dlo, "det_ci_hi": dhi})
        return pd.DataFrame(rows)

    def real_fpr_table(self):
        flag = (self.r["score"].to_numpy() >= self.thr).astype(float)
        rows, gaps = [], []
        for attr in ATTRS:
            levs, means, reps = [], [], []
            for lev, d in self.r[self.r[attr] != ""].groupby(attr):
                idx = d.index.to_numpy()
                pt, rp = self.gb_r.mean(flag[idx], self.r["identity"].to_numpy()[idx])
                lo, hi = ci(rp) if d["identity"].nunique() >= 2 else (np.nan, np.nan)
                rows.append({"attribute": attr, "level": lev, "n_renders": len(d),
                             "n_identities": d["identity"].nunique(), "fpr": pt,
                             "ci_lo": lo, "ci_hi": hi})
                if d["identity"].nunique() >= 2:
                    levs.append(lev); means.append(pt); reps.append(rp)
            if len(levs) >= 2:
                a = np.vstack(reps)
                with np.errstate(invalid="ignore"):
                    g_reps = np.nanmax(a, 0) - np.nanmin(a, 0)
                glo, ghi = ci(g_reps)
                i_max, i_min = int(np.nanargmax(means)), int(np.nanargmin(means))
                gaps.append({"attribute": attr, "n_levels": len(levs), "fpr_gap": gap(means),
                             "ci_lo": glo, "ci_hi": ghi, "max_level": levs[i_max],
                             "max_fpr": means[i_max], "min_level": levs[i_min],
                             "min_fpr": means[i_min]})
        return pd.DataFrame(rows), pd.DataFrame(gaps)

    def subgroup_auc_tables(self):
        rows, worst = [], []
        for gen in self.gens():
            for attr in ATTRS:
                levs, pts, reps = [], [], []
                for lev in sorted((set(self.f[attr]) | set(self.r[attr])) - {""}):
                    fm, rm = self._sel(gen, (self.f[attr] == lev).to_numpy(),
                                       (self.r[attr] == lev).to_numpy())
                    r_n, r_id = int(rm.sum()), self.r.loc[rm, "identity"].nunique()
                    if r_n < MIN_REAL or fm.sum() == 0:
                        rows.append({"generator": gen, "attribute": attr, "level": lev,
                                     "n_fake": int(fm.sum()), "n_real": r_n, "n_real_identities": r_id,
                                     "auc": np.nan, "ci_lo": np.nan, "ci_hi": np.nan,
                                     "note": f"not estimable: {r_n} real renders (< {MIN_REAL})"})
                        continue
                    pt, rp = auc_reps(self.f["score"].to_numpy()[fm], self.r["score"].to_numpy()[rm],
                                      self.Wf[:, fm], self.Wr[:, rm])
                    lo, hi = ci(rp)
                    rows.append({"generator": gen, "attribute": attr, "level": lev,
                                 "n_fake": int(fm.sum()), "n_real": r_n, "n_real_identities": r_id,
                                 "auc": pt, "ci_lo": lo, "ci_hi": hi, "note": ""})
                    levs.append(lev); pts.append(pt); reps.append(rp)
                if len(levs) >= 2:
                    a = np.vstack(reps)
                    with np.errstate(invalid="ignore"):
                        w_reps, g_reps = np.nanmin(a, 0), np.nanmax(a, 0) - np.nanmin(a, 0)
                    i_min, i_max = int(np.nanargmin(pts)), int(np.nanargmax(pts))
                    wl, wh = ci(w_reps)
                    gl, gh = ci(g_reps)
                    worst.append({"generator": gen, "attribute": attr, "n_levels": len(levs),
                                  "worst_level": levs[i_min], "worst_auc": pts[i_min],
                                  "worst_ci_lo": wl, "worst_ci_hi": wh, "best_level": levs[i_max],
                                  "best_auc": pts[i_max], "auc_gap": pts[i_max] - pts[i_min],
                                  "gap_ci_lo": gl, "gap_ci_hi": gh})
        return pd.DataFrame(rows), pd.DataFrame(worst)

    def roc_points(self):
        from sklearn.metrics import roc_curve
        out = {}
        for gen in self.gens():
            fm, rm = self._sel(gen)
            f, r = self.f["score"].to_numpy()[fm], self.r["score"].to_numpy()[rm]
            if len(f) and len(r):
                fpr, tpr, _ = roc_curve(np.r_[np.ones(len(f)), np.zeros(len(r))], np.r_[f, r])
                out[gen] = (fpr, tpr)
        return out
