#!/usr/bin/env python
"""Build the Counterfactual DeepFake Bench controlled-synthetic prompt matrix.

Design
------
The unit of design is the COUNTERFACTUAL GROUP (plan 5.2): one group fixes
scene, lighting, behaviour, attire-slot, camera and duration, then instantiates
that identical content across all 56 demographic cells, sharing one seed.

This buys confound balancing for free (plan 5.3): because every cell appears
exactly once in every group, every cell sees a bit-identical distribution of
settings, lighting, behaviours, camera moves and durations. No Latin square
needed - balance is structural, not sampled.

  clips = groups x 56

Usage
-----
  python build_matrix.py --model ltx23 --groups 36 --out ../manifests/prompt_matrix_ltx23.json
"""
import argparse, csv, hashlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from taxonomy import (RACES, GENDERS, AGE_BANDS, HAIR, SETTINGS, LIGHTING, article,
                      BEHAVIORS, ATTIRE, CAMERA, RESOLUTION, LTX_LENGTHS,
                      LTX_FPS, cell_id)


def stable_seed(*parts, bits=63):
    """Deterministic seed from strings - reproducible across runs and machines."""
    h = hashlib.blake2b("||".join(str(p) for p in parts).encode(), digest_size=8)
    return int.from_bytes(h.digest(), "big") >> (64 - bits)


def balanced_assign(n_levels, groups, salt):
    """Assign a level to each group: near-equal counts, deterministically shuffled.

    Modular strides (g * k % n) are a trap - whenever gcd(k, n) > 1 they cover
    only n/gcd levels, silently dropping bank entries, and two fields driven by
    strides over the same g become correlated with each other. Building balanced
    lists and shuffling each independently gives balanced marginals AND
    decorrelated fields.
    """
    base = [i % n_levels for i in range(groups)]
    # Fisher-Yates driven by a stable per-field hash - no Random(), no global state
    for i in range(len(base) - 1, 0, -1):
        j = stable_seed(salt, i, bits=32) % (i + 1)
        base[i], base[j] = base[j], base[i]
    return base


def build(model, groups, lengths, fps, resolution):
    specs = []
    a_set = balanced_assign(len(SETTINGS), groups, f"{model}/setting")
    a_beh = balanced_assign(len(BEHAVIORS), groups, f"{model}/behavior")
    a_cam = balanced_assign(len(CAMERA), groups, f"{model}/camera")
    a_att = balanced_assign(len(ATTIRE), groups, f"{model}/attire")

    # Lighting and duration are balanced JOINTLY, not independently. Both are
    # technical factors a detector is sensitive to, and lighting x skin-tone is
    # the interaction plan 5.3 singles out - so they must stay orthogonal.
    # Independent shuffling left low-light 280/56 skewed toward short clips.
    n_joint = len(LIGHTING) * len(lengths)
    a_joint = balanced_assign(n_joint, groups, f"{model}/lighting_x_length")
    a_lit = [j // len(lengths) for j in a_joint]
    a_len = [j % len(lengths) for j in a_joint]

    for g in range(groups):
        # One shared content combination per group, identical across all 56 cells.
        setting = SETTINGS[a_set[g]]
        lighting = LIGHTING[a_lit[g]]
        behavior = BEHAVIORS[a_beh[g]]
        camera = CAMERA[a_cam[g]]
        attire_slot = a_att[g]
        length = lengths[a_len[g]]
        group_seed = stable_seed(model, "group", g)

        for rk, race_phrase in RACES:
            for gk, gword, gposs in GENDERS:
                for ak, age_phrases, age_detail, age_tier in AGE_BANDS:
                    # age phrase varies by group so a cell is not one fixed phrase
                    age_phrase = age_phrases[g % len(age_phrases)].format(poss=gposs)
                    hair_opts = HAIR[rk][gk][age_tier]
                    hair = hair_opts[g % len(hair_opts)]
                    cid = cell_id(rk, gk, ak)
                    pid = f"{model}__{cid}__g{g:03d}"
                    specs.append({
                        "prompt_id": pid,
                        "model": model,
                        "cell": cid,
                        "counterfactual_group": g,
                        "demographic": {
                            "race": rk, "race_phrase": race_phrase,
                            "article": article(race_phrase),
                            "gender": gk, "gender_word": gword,
                            "age_band": ak, "age_phrase": age_phrase,
                            "age_detail": age_detail, "age_tier": age_tier,
                        },
                        "appearance": {"hair": hair, "attire": ATTIRE[attire_slot]},
                        "scene": {"setting_key": setting[0], "setting": setting[1],
                                  "lighting_key": lighting[0], "lighting": lighting[1]},
                        "camera": {"key": camera[0], "framing": camera[1]},
                        "action": {"key": behavior[0], "behavior": behavior[1],
                                   "audio": behavior[2]},
                        # seed shared across all 56 cells of the group (plan 5.2)
                        "seed": group_seed,
                        "width": resolution[0], "height": resolution[1],
                        "length": length, "fps": fps,
                        "duration_s": round(length / fps, 2),
                        "ai_generated": True,
                    })
    return specs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ltx23")
    ap.add_argument("--groups", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv", default=None)
    a = ap.parse_args()

    specs = build(a.model, a.groups, LTX_LENGTHS, LTX_FPS, RESOLUTION)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(specs, open(a.out, "w"), indent=1)

    # ---- balance assertions: the whole point of the design
    from collections import Counter
    cells = Counter(s["cell"] for s in specs)
    assert len(cells) == 56, f"expected 56 cells, got {len(cells)}"
    assert len(set(cells.values())) == 1, f"cells unbalanced: {set(cells.values())}"
    for field, get in [("setting", lambda s: s["scene"]["setting_key"]),
                       ("lighting", lambda s: s["scene"]["lighting_key"]),
                       ("behavior", lambda s: s["action"]["key"]),
                       ("length", lambda s: s["length"])]:
        per_cell = {}
        for s in specs:
            per_cell.setdefault(s["cell"], Counter())[get(s)] += 1
        dists = {tuple(sorted(c.items())) for c in per_cell.values()}
        assert len(dists) == 1, f"{field} distribution differs across cells"

    # COVERAGE: every bank level must actually appear. The cross-cell balance
    # check above passes even when a modular stride silently uses only a subset
    # of a bank, which is exactly how the (g*3)%6 lighting bug hid - it dropped
    # backlit and low-light, the two conditions plan 5.3 cares most about.
    banks = [("setting", SETTINGS, lambda s: s["scene"]["setting_key"]),
             ("lighting", LIGHTING, lambda s: s["scene"]["lighting_key"]),
             ("behavior", BEHAVIORS, lambda s: s["action"]["key"]),
             ("camera", CAMERA, lambda s: s["camera"]["key"])]
    for name, bank, get in banks:
        want = {b[0] for b in bank}
        got = {get(s) for s in specs}
        missing = want - got
        assert not missing, (f"{name}: {len(missing)} of {len(want)} levels never "
                             f"generated: {sorted(missing)}")
        counts = Counter(get(s) for s in specs)
        lo, hi = min(counts.values()), max(counts.values())
        spread = hi / lo if lo else float("inf")
        assert spread <= 2.0, f"{name} marginals too skewed: {counts}"
        print(f"  {name:9s} {len(got)}/{len(want)} levels, "
              f"per-level {lo}-{hi} clips")

    # Orthogonality of lighting x duration: not merely "co-occurs more than once"
    # but actually balanced, so duration cannot proxy for lighting.
    pairs = Counter((s["scene"]["lighting_key"], s["length"]) for s in specs)
    lo, hi = min(pairs.values()), max(pairs.values())
    assert hi / lo <= 1.5, (
        f"lighting x duration not orthogonal (cell counts {lo}-{hi}): {dict(pairs)}")
    print(f"  lighting x duration orthogonal: all {len(pairs)} combinations "
          f"{lo}-{hi} clips")

    print(f"{len(specs)} specs | {a.groups} counterfactual groups x 56 cells "
          f"| {cells.most_common(1)[0][1]} clips/cell")
    print("balance OK: every cell has an identical distribution of "
          "setting, lighting, behavior and duration")
    print(f"wrote {a.out}")

    if a.csv:
        keys = ["prompt_id", "model", "cell", "counterfactual_group", "seed",
                "width", "height", "length", "fps", "duration_s"]
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for s in specs:
                w.writerow(s)
        print(f"wrote {a.csv}")


if __name__ == "__main__":
    main()
