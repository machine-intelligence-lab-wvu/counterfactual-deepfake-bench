"""FairFace labels for raw CelebV-HQ segments that filter_real.py rejected.

Same face crops (label_strata.face_crops) and classifier as --stage label, but read
from the raw segment, so the unfiltered real set has a label for every clip it can.
Writes one <clip_id>.json per clip with the same `demographic` record.

  python real/label_raw.py --raw ../celebvhq_raw --report ../fairdeep-bench/qc_report_real.csv \
      --out ../fairdeep-bench/real_raw_labels --weights <res34_fair_align_multi_7>.pt
"""
import argparse, csv, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fairface import FairFace  # noqa: E402
from label_strata import face_crops, yunet_model  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--report", required=True, help="filter_real.py qc report")
    ap.add_argument("--out", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(a.report)) if r["accepted"] != "1"]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ff, model = FairFace(a.weights, device=a.device), yunet_model()
    print(f"labelling {len(rows)} rejected clips from raw on {ff.device}", flush=True)
    for i, r in enumerate(rows, 1):
        dst = out / f"{r['clip']}.json"
        if dst.exists():
            continue
        res = ff.predict_clip(face_crops(str(Path(a.raw) / f"{r['clip']}.mp4"), model))
        dst.write_text(json.dumps({"clip_id": r["clip"], "filter_reason": r["reason"],
                                   "demographic": res, "cell": res.get("cell")}, indent=1))
        if i % 50 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
