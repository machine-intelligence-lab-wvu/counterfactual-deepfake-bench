"""Presentation summary for one view: AUC per generator (fps-matched reals), all reals vs the
filter-accepted subset, and real FPR by perceived subgroup at the 5%-FPR threshold.
Point estimates only; CIs are in the snapshot REPORT.md.

  python eval/present_real_all.py <view> [<view> ...]
"""
import sys
import pandas as pd
from sklearn.metrics import roc_auc_score

R = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
man = pd.read_csv(f"{R}/eval/manifests/real_all.csv")
man = man.set_index("clip_id")
GEN_FPS = {"ltx23": 24, "wan22": 16, "hunyuan15": 24, "ltx25": 24}
NAMES = {"ltx23": "LTX 2.3", "wan22": "Wan 2.2", "hunyuan15": "HunyuanVideo 1.5", "ltx25": "LTX 2.5"}

for view in sys.argv[1:]:
    print(f"\n## View `{view}`\n")
    rows, fprs = [], []
    for det in ["decof", "demamba"]:
        s = pd.read_csv(f"{R}/results/snapshots/{det}/{view}/latest/scores.csv")
        fk = s[(s.batch != "real_all") & (s.generator != "real") & (s.primary == 1)]
        rl = s[s.batch == "real_all"].copy()
        rl["src"] = rl.clip_id.str.replace(r"__fps\d+$", "", regex=True)
        rl["fps"] = rl.clip_id.str.extract(r"__fps(\d+)$")[0].astype(int)
        rl = rl.join(man[["filter_accepted", "race", "gender", "age_band"]], on="src")
        for gen in list(GEN_FPS) + ["all"]:
            f = fk if gen == "all" else fk[fk.generator == gen]
            r = rl if gen == "all" else rl[rl.fps == GEN_FPS[gen]]
            rf = r[r.filter_accepted == 1]
            auc = lambda ff, rr: roc_auc_score([1] * len(ff) + [0] * len(rr),
                                               list(ff.score) + list(rr.score))
            rows.append({"detector": det, "generator": NAMES.get(gen, "all"),
                         "n_fake": len(f), "n_real_all": r.src.nunique(),
                         "AUC all reals": round(auc(f, r), 3),
                         "n_real_filtered": rf.src.nunique(),
                         "AUC filtered reals": round(auc(f, rf), 3)})
        thr = rl.score.quantile(0.95)
        for attr in ["race", "gender", "age_band"]:
            for lev, d in rl[rl[attr].notna() & (rl[attr] != "")].groupby(attr):
                fprs.append({"detector": det, "attribute": attr, "level": lev,
                             "n_clips": d.src.nunique(), "real FPR": round((d.score >= thr).mean(), 3)})
    print(pd.DataFrame(rows).to_markdown(index=False))
    print("\nReal false-positive rate by perceived subgroup (threshold = 5% FPR over all reals):\n")
    t = pd.DataFrame(fprs).pivot_table(index=["attribute", "level", "n_clips"], columns="detector",
                                       values="real FPR").reset_index()
    print(t.to_markdown(index=False))
