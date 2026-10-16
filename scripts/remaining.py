#!/usr/bin/env python
"""Subtract the clips a run already produced from its matrix.

The driver skips clips whose .mp4 is already on disk, which is enough to
resubmit on the same cluster. Moving the tail of a run somewhere else needs
the list in a file instead, because the new cluster's output tree is empty:
this writes a matrix holding only the specs that are still missing.

Completed clips are taken from the run logs (ok records) and, with --root,
from an output tree as well - the union, so a log lost to a dead node does
not cause a clip to be generated twice.

  python scripts/remaining.py --matrix manifests/prompt_matrix_hunyuan15_sub504b.json \
      --logs 'manifests/generation_log_hunyuan15b_s*.jsonl' \
      --out manifests/prompt_matrix_hunyuan15_sub504b_rest.json
"""
import argparse, collections, glob, json, os


def completed(log_glob, root):
    done = set()
    for path in sorted(glob.glob(log_glob)):
        for line in open(path):
            line = line.strip()
            if line and json.loads(line).get("ok"):
                done.add(json.loads(line)["prompt_id"])
    if root:
        done |= {os.path.basename(p)[:-4]
                 for p in glob.glob(os.path.join(root, "**", "*.mp4"), recursive=True)}
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--logs", default="", help="glob of generation_log_*.jsonl")
    ap.add_argument("--root", default="", help="also count .mp4 files under this tree")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.logs and not a.root:
        ap.error("give --logs, --root or both")

    specs = json.load(open(a.matrix))
    done = completed(a.logs, a.root)
    rest = [s for s in specs if s["prompt_id"] not in done]
    json.dump(rest, open(a.out, "w"), indent=1)

    groups = collections.Counter(s["counterfactual_group"] for s in rest)
    print(f"{len(specs)} specs, {len(specs) - len(rest)} done, {len(rest)} remaining")
    print("  per group: " + ", ".join(f"{g}:{n}" for g, n in sorted(groups.items())))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
