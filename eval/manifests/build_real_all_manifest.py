#!/usr/bin/env python
"""Build the unfiltered real batch (real_all): every fetched CelebV-HQ segment.

real_b1 holds only the clips filter_real.py accepted, cut to their clean run. real_all
keeps every raw segment, whatever the filter said, so the filtered and unfiltered real sets
can be compared on the same detectors and views. The filter's verdict is carried per clip
(filter_accepted, filter_reason) instead of being applied.

Labels: FairFace on the conformed copy for accepted clips (real-half `--stage label`), on the
raw segment for rejected clips (real-half `real/label_raw.py`); label_source says which.

  primary = 1 for every clip (no filtering). Clips without a taxonomy cell (no face, or FairFace
  age 0-19) still count in overall metrics; subgroup tables skip empty labels.

  python -m eval.manifests.build_real_all_manifest --raw <celebvhq_raw> \
      --report <qc_report_real.csv> --accepted <deepfake-bench-data/real> \
      --rejected <deepfake-bench-data/real_raw_labels> --info <celebvhq_info.json>
"""
import argparse
import csv
import json
import os

import pandas as pd

from eval.common import MANIFEST_DIR
from eval.manifests.build_real_manifest import probe


def build(batch, raw, report, accepted, rejected, info):
    ytb = {k: v["ytb_id"] for k, v in json.load(open(info))["clips"].items()}
    rows = []
    for r in csv.DictReader(open(report)):
        cid, ok = r["clip"], r["accepted"] == "1"
        src = os.path.join(os.path.abspath(raw), cid + ".mp4")
        if not os.path.exists(src):
            continue
        sc = os.path.join(accepted if ok else rejected, cid + ".json")
        dm = (json.load(open(sc)).get("demographic") or {}) if os.path.exists(sc) else {}
        labelled = bool(dm.get("ok")) and bool(dm.get("cell"))
        confs = [dm.get("fairface_race_conf"), dm.get("fairface_gender_conf"),
                 dm.get("fairface_age_conf")]
        w, h, fps, dur = probe(src)
        rows.append({
            "clip_id": f"celebvhq__{cid}", "batch": batch, "label": 0, "source_id": cid,
            "path": src,
            "perceived_race": dm.get("race", ""), "perceived_gender": dm.get("gender", ""),
            "perceived_age_band": dm.get("age_band", ""),
            "label_confidence": min(c for c in confs if c is not None) if labelled else "",
            "width": w, "height": h, "fps": fps, "duration_s": round(dur, 3),
            "face_gate": int(ok), "primary": 1,
            "identity_cluster": ytb.get(cid, cid), "generator": "real",
            "race": dm.get("race", ""), "gender": dm.get("gender", ""),
            "age_band": dm.get("age_band", ""), "cell": dm.get("cell") or "",
            "race_conf": confs[0], "gender_conf": confs[1], "age_conf": confs[2],
            "age_ambiguous": dm.get("age_ambiguous", ""),
            "age_band_alt": dm.get("age_band_alt") or "",
            "cell_excluded_reason": dm.get("cell_excluded_reason") or ("" if dm else "no label"),
            "labelled": int(labelled),
            "label_source": ("conformed" if ok else "raw") if dm else "",
            "filter_accepted": int(ok), "filter_reason": r["reason"],
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default="real_all")
    ap.add_argument("--raw", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--accepted", required=True)
    ap.add_argument("--rejected", required=True)
    ap.add_argument("--info", required=True)
    a = ap.parse_args()
    df = build(a.batch, a.raw, a.report, a.accepted, a.rejected, a.info)
    out = os.path.join(MANIFEST_DIR, f"{a.batch}.csv")
    df.to_csv(out, index=False)
    print(f"{out}: {len(df)} clips, filter-accepted {int(df['filter_accepted'].sum())}, "
          f"labelled {int(df['labelled'].sum())}, "
          f">= 5 s {int((df['duration_s'] >= 5.0 - 1e-3).sum())}, "
          f">= 2 s {int((df['duration_s'] >= 2.0 - 1e-3).sum())}, "
          f"videos {df['identity_cluster'].nunique()}")


if __name__ == "__main__":
    main()
