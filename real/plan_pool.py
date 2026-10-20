"""Turn celebvhq_info.json into an ordered download manifest.

Bandwidth is the scarce resource, so the order matters more than the filter.
CelebV-HQ is YouTube footage and skews young, male and white; the taxonomy wants
56 equal cells. Downloading the pool in its natural order spends the first
several hours on `white__m__30-44` and still leaves the 60+ cells empty.

So clips are ordered by how *scarce* their predicted cell is. The index ships
40 CelebA-style appearance flags, three of which are priors on the taxonomy
axes: `male` (gender), `young` and `gray_hair` (age). Race is not annotated, so
it cannot be prioritised here - FairFace supplies it after download, and the
race imbalance has to be absorbed by over-fetching.

The priors are weak - CelebA's `young` is a single binary cut, not four bands -
so this is a download *order*, never a label. Every demographic label comes from
FairFace in label_strata.py.

    python real/plan_pool.py --info celebvhq_info.json --out manifests/celebvhq_pool.json
"""
import argparse, json, random
from collections import Counter

TARGET_DUR = 6.04   # the synthetic clips' length; see specs/taxonomy.py


def build(info, min_dur, drop_blurry, pad):
    am = info["meta_info"]["appearance_mapping"]
    iM, iY, iB, iG = (am.index("male"), am.index("young"),
                      am.index("blurry"), am.index("gray_hair"))
    out = []
    for cid, c in info["clips"].items():
        d = c["duration"]
        dur = d["end_sec"] - d["start_sec"]
        if dur < min_dur:
            continue
        a = c["attributes"]["appearance"]
        if drop_blurry and a[iB]:
            continue
        male, young, gray = bool(a[iM]), bool(a[iY]), bool(a[iG])

        # Scarcity weight. gray_hair is the only signal for the 60+ band, which
        # is the binding constraint (11.4% of the pool for 14 of 56 cells), so
        # it dominates. Female is ~36% of the pool, hence the smaller boost.
        w = 1.0
        if gray:
            w *= 6.0
        if not young:
            w *= 1.8
        if not male:
            w *= 1.6
        out.append({
            "clip_id": cid,
            "ytb_id": c["ytb_id"],
            # pad the request so our own window picker has slack to find a clean
            # TARGET_DUR run inside the annotated shot
            "start_sec": round(max(0.0, d["start_sec"] - pad), 2),
            "end_sec": round(d["end_sec"] + pad, 2),
            "ann_start_sec": d["start_sec"],
            "ann_end_sec": d["end_sec"],
            "ann_duration": round(dur, 2),
            "bbox": c["bbox"],
            "prior": {"male": male, "young": young, "gray_hair": gray},
            "weight": round(w, 3),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True, help="celebvhq_info.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-dur", type=float, default=TARGET_DUR,
                    help=f"drop clips shorter than this (default {TARGET_DUR})")
    ap.add_argument("--pad", type=float, default=0.5,
                    help="seconds of slack fetched either side of the annotated shot")
    ap.add_argument("--keep-blurry", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    info = json.load(open(a.info, encoding="utf-8"))
    pool = build(info, a.min_dur, not a.keep_blurry, a.pad)

    # Weighted shuffle: sort by weight/Expo(1), which orders by weight in
    # expectation without making the result a rigid ranking - two runs explore
    # different clips of the same scarcity class.
    rng = random.Random(a.seed)
    pool.sort(key=lambda r: -r["weight"] / max(rng.expovariate(1.0), 1e-9))

    for i, r in enumerate(pool):
        r["rank"] = i

    json.dump({"target_dur": TARGET_DUR, "n": len(pool), "clips": pool},
              open(a.out, "w"), indent=1)

    pr = Counter()
    for r in pool[:5000]:
        p = r["prior"]
        pr["gray_hair" if p["gray_hair"] else "-"] += 1
        pr["female" if not p["male"] else "-"] += 1
    print(f"pool {len(pool)} clips, {len({r['ytb_id'] for r in pool})} source videos")
    print(f"  est download {sum(r['end_sec']-r['start_sec'] for r in pool)*0.35/1024:.1f} GB "
          f"at the measured ~0.35 MB per second of 1080p video")
    print(f"  in the first 5000 by order: gray_hair={pr['gray_hair']} female={pr['female']}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
