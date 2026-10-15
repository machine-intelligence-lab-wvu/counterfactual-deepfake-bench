#!/usr/bin/env python
"""Derive a matched prompt matrix for another generator from an existing one.

Every spec keeps its cell, counterfactual group, content (scene, lighting,
behaviour, attire, camera, hair, age phrase) and seed; only the model, frame
rate and frame count change, with frame count chosen to preserve duration. So
across the two matrices the generator is the only varied factor.

  python derive_matrix.py --src ../manifests/prompt_matrix_ltx23.json \
      --model wan22 --out ../manifests/prompt_matrix_wan22.json
"""
import argparse, copy, json

# per-model fps and length rule (frames for a target duration)
MODELS = {
    "wan22": {"fps": 16, "stride": 4, "width": 1280, "height": 704},
    "hunyuan15": {"fps": 24, "stride": 4, "width": 1280, "height": 704},
}


def derive(src, model):
    m = MODELS[model]
    out = []
    for s in src:
        d = copy.deepcopy(s)
        # nearest stride*k+1 frame count to the source duration
        k = round(s["duration_s"] * m["fps"] / m["stride"])
        length = m["stride"] * k + 1
        d.update(model=model, fps=m["fps"], length=length,
                 width=m["width"], height=m["height"],
                 duration_s=round(length / m["fps"], 2),
                 prompt_id=s["prompt_id"].replace(s["model"], model, 1),
                 derived_from=s["prompt_id"])
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    specs = derive(json.load(open(a.src)), a.model)
    json.dump(specs, open(a.out, "w"), indent=1)
    from collections import Counter
    print(f"{len(specs)} specs, lengths {dict(Counter(s['length'] for s in specs))} "
          f"@ {specs[0]['fps']} fps -> {a.out}")


if __name__ == "__main__":
    main()
