"""Label filtered real clips with FairFace and select a stratified subset.

Two stages, because they fail differently:

  --stage label   run FairFace over every filtered clip, write the full
                  probability distributions into each sidecar. GPU-bound, done
                  once, never repeated when the targets change.
  --stage select  choose a subset hitting --per-cell across the 56 cells, write
                  the selection and an honest coverage report. Cheap, re-runnable.

Keeping selection out of inference matters: the cells CelebV-HQ cannot fill are
discovered here, and the response to that is to re-run `select` with different
targets, not to re-infer 10,000 clips.

A note that belongs in the paper, not just the code: these are FairFace's
*perceived* labels on real people who did not self-identify for this dataset.
The synthetic half's demographics are prompted and then verified; the real
half's are inferred only. The two halves therefore carry different label
provenance, and a subgroup result that compares them must say so.

    python real/label_strata.py --stage label  --clips <dir> --weights <fairface.pth>
    python real/label_strata.py --stage select --clips <dir> --per-cell 90
"""
import argparse, csv, glob, json, sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fairface import FairFace  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "specs"))
import taxonomy  # noqa: E402

N_CROPS = 8          # face crops per clip, spread over its length
CROP_MARGIN = 0.35   # FairFace was trained on padded crops, not tight boxes


def face_crops(path, model, n=N_CROPS):
    """Sample n face crops across the clip, padded the way FairFace expects."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total <= 0:
        cap.release()
        return []
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    det = cv2.FaceDetectorYN.create(model, "", (w, h), 0.6, 0.3, 5000)
    want = set(np.linspace(0, total - 1, min(n, total)).round().astype(int).tolist())

    crops, i = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i in want:
            _, faces = det.detect(frame)
            if faces is not None and len(faces):
                f = max(faces, key=lambda r: r[3])
                x, y, bw, bh = f[0], f[1], f[2], f[3]
                mx, my = bw * CROP_MARGIN, bh * CROP_MARGIN
                x0, y0 = int(max(0, x - mx)), int(max(0, y - my))
                x1, y1 = int(min(w, x + bw + mx)), int(min(h, y + bh + my))
                if x1 > x0 and y1 > y0:
                    crops.append(frame[y0:y1, x0:x1])
        i += 1
    cap.release()
    return crops


def yunet_model():
    p = Path(__file__).parent / "models" / "face_detection_yunet_2023mar.onnx"
    if not p.exists():
        import urllib.request
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(
            "https://huggingface.co/opencv/face_detection_yunet/resolve/main/"
            "face_detection_yunet_2023mar.onnx", p)
    return str(p)


def stage_label(a):
    ff = FairFace(a.weights, device=a.device)
    model = yunet_model()
    sides = sorted(glob.glob(str(Path(a.clips) / "*.json")))
    print(f"labelling {len(sides)} clips on {ff.device}")

    done = 0
    for i, sp in enumerate(sides, 1):
        side = json.loads(Path(sp).read_text())
        if side.get("demographic") and not a.overwrite:
            continue
        mp4 = Path(sp).with_suffix(".mp4")
        if not mp4.exists():
            continue
        crops = face_crops(str(mp4), model)
        res = ff.predict_clip(crops)
        side["demographic"] = res
        side["cell"] = res.get("cell")
        Path(sp).write_text(json.dumps(side, indent=1))
        done += 1
        if i % 50 == 0 or i == len(sides):
            print(f"  {i}/{len(sides)}  labelled {done}", flush=True)
    print(f"labelled {done} clips")


def stage_select(a):
    sides = sorted(glob.glob(str(Path(a.clips) / "*.json")))
    rows = []
    for sp in sides:
        s = json.loads(Path(sp).read_text())
        d = s.get("demographic") or {}
        if not d.get("ok"):
            continue
        rows.append({
            "clip": s["clip_id"], "cell": d.get("cell"),
            "race": d.get("race"), "gender": d.get("gender"),
            "age_band": d.get("age_band"),
            "age_ambiguous": d.get("age_ambiguous", 0),
            "race_conf": d.get("fairface_race_conf", 0.0),
            "gender_conf": d.get("fairface_gender_conf", 0.0),
            "age_conf": d.get("fairface_age_conf", 0.0),
            "fps": s.get("fps"), "upscale": s.get("conformance", {}).get("upscale"),
        })

    by_cell = defaultdict(list)
    for r in rows:
        if r["cell"]:
            by_cell[r["cell"]].append(r)
    # Highest-confidence clips first: when a cell is over-subscribed, the clips
    # the classifier is surest about are the ones worth keeping.
    for v in by_cell.values():
        v.sort(key=lambda r: -(r["race_conf"] * r["gender_conf"] * r["age_conf"]))

    all_cells = [taxonomy.cell_id(r, g, ag) for r, g, ag in taxonomy.cells()]
    chosen, short = [], []
    for cell in all_cells:
        avail = by_cell.get(cell, [])
        if a.min_conf:
            avail = [r for r in avail
                     if r["race_conf"] >= a.min_conf and r["gender_conf"] >= a.min_conf]
        if a.exclude_ambiguous:
            avail = [r for r in avail if not r["age_ambiguous"]]
        take = avail[:a.per_cell]
        chosen.extend(take)
        if len(take) < a.per_cell:
            short.append((cell, len(take), a.per_cell - len(take)))

    out = Path(a.out or Path(a.clips).parent / "strata_selection.csv")
    keys = ["clip", "cell", "race", "gender", "age_band", "age_ambiguous",
            "race_conf", "gender_conf", "age_conf", "fps", "upscale"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in chosen:
            w.writerow(r)

    cov = Path(a.coverage or Path(a.clips).parent / "cell_coverage_real.csv")
    with open(cov, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "race", "gender", "age_band", "available", "selected",
                    "target", "shortfall"])
        for cell in all_cells:
            r, g, ag = cell.split("__")
            av = len(by_cell.get(cell, []))
            se = min(av, a.per_cell)
            w.writerow([cell, r, g, ag, av, se, a.per_cell, max(0, a.per_cell - se)])

    print(f"labelled clips: {len(rows)}   with a cell: {sum(1 for r in rows if r['cell'])}")
    print(f"selected {len(chosen)} / target {a.per_cell * 56}")
    excl = Counter(json.loads(Path(sp).read_text()).get("demographic", {})
                   .get("cell_excluded_reason") for sp in sides)
    for k, v in excl.most_common():
        if k:
            print(f"  excluded: {v:5d}  {k}")
    if short:
        print(f"\n{len(short)} of 56 cells under target:")
        for cell, have, miss in sorted(short, key=lambda t: -t[2])[:20]:
            print(f"  {cell:34s} have {have:4d}  short {miss:4d}")
    print(f"\nwrote {out}\nwrote {cov}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["label", "select"], required=True)
    ap.add_argument("--clips", required=True, help="dir of filtered clips + sidecars")
    ap.add_argument("--weights", help="FairFace res34 7-race checkpoint (label stage)")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--per-cell", type=int, default=90,
                    help="90 x 56 cells = 5,040 clips")
    ap.add_argument("--min-conf", type=float, default=0.0,
                    help="drop clips FairFace is unsure about")
    ap.add_argument("--exclude-ambiguous", action="store_true",
                    help="drop FairFace 40-49, which straddles the 44/45 cell boundary")
    ap.add_argument("--out", default=None)
    ap.add_argument("--coverage", default=None)
    a = ap.parse_args()

    if a.stage == "label":
        if not a.weights:
            ap.error("--weights is required for --stage label")
        stage_label(a)
    else:
        stage_select(a)


if __name__ == "__main__":
    main()
