#!/usr/bin/env python
"""results/coverage.md: scored / pending / failed per batch x detector x view.

Updated by eval.run and eval.aggregate; `python -m eval.coverage` rebuilds it by hand.
"""
import os

import pandas as pd

from eval.common import REPO, RESULTS, eval_sets, utc_now
from eval.detectors import registry

VIEWS = ["native", "face512", "native_2s", "face512_2s"]


def _counts(batch, info, det_name, view):
    from eval.preprocess import latest_records
    from eval.run import read_scores
    from eval.views.spec import load as load_view
    man_path = os.path.join(REPO, info["manifest"])
    if not os.path.exists(man_path):
        return {"clips": "-", "rendered": "-", "excluded": "-", "render_failed": "-",
                "scored": "-", "score_failed": "-", "pending": "batch pending"}
    n = len(pd.read_csv(man_path, usecols=["clip_id"]))
    vh = load_view(view, check_toolchain=False)["view_hash"]
    pre = latest_records(view, batch, vh)
    st = pre["status"].value_counts().to_dict() if not pre.empty else {}
    rendered = int(st.get("ok", 0))
    try:
        det = registry.get(det_name)
    except Exception:
        det = None
    sc = read_scores(det_name, view, batch)
    if det is not None and not sc.empty:
        sc = sc[(sc["checkpoint_sha256"] == det.checkpoint_sha256)
                & (sc["detector_version"] == det.version) & (sc["view_hash"] == vh)]
        last = sc.sort_values("timestamp").groupby("clip_id").tail(1)
        ok, fail = int((last["status"] == "ok").sum()), int((last["status"] != "ok").sum())
    else:
        ok, fail = 0, 0
    if info["kind"] == "real":
        n_out = n * len(load_view(view, check_toolchain=False)["fps"]["real"])
        n = f"{n} ({n_out} renders)"
    pending = rendered - ok - fail
    impl = det is not None and det.implemented
    return {"clips": n, "rendered": rendered, "excluded": int(st.get("excluded", 0)),
            "render_failed": int(st.get("failed", 0)), "scored": ok, "score_failed": fail,
            "pending": pending if impl else "detector not implemented"}


def write_coverage():
    sets = eval_sets()
    rows = []
    for batch, info in sets["batches"].items():
        for det in registry.REGISTRY:
            for view in VIEWS:
                rows.append({"batch": batch, "detector": det, "view": view,
                             **_counts(batch, info, det, view)})
    df = pd.DataFrame(rows)
    lines = [f"# Coverage\n", f"Updated {utc_now()}. Active batches: {', '.join(sets['active'])}.",
             "`rendered` = view videos that passed ffprobe verification; `excluded` = clips the "
             "view rules exclude (e.g. no face for face512); `pending` = rendered but not yet "
             "scored by this detector.\n", df.to_markdown(index=False)]
    out = os.path.join(RESULTS, "coverage.md")
    os.makedirs(RESULTS, exist_ok=True)
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return out


if __name__ == "__main__":
    print(write_coverage())
