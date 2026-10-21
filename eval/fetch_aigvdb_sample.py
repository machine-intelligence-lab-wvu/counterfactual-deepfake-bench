#!/usr/bin/env python
"""Fetch a seeded sample of AIGVDBench test videos straight out of the release zips (HTTP range
reads through HfFileSystem; nothing else is downloaded).

  python -m eval.fetch_aigvdb_sample --out <dir> --n 150 [--seed 20261021]

Layout written: <out>/Real/<id> and <out>/Fake/<MOD>_<generator>/<id> for the 20 Open-Source
generators (T2V 12, I2V 6, V2V 2), the same Video_ids in every source, drawn from Split/test.jsonl.
That is the layout eval.sanity_genvideo reads.
"""
import argparse
import json
import os
import random
import zipfile
from concurrent.futures import ThreadPoolExecutor

from huggingface_hub import HfFileSystem, hf_hub_download

REPO, REV = "AIGVDBench/AIGVDBench", "bf48acaa4920990af3dd2a511ea88e63354df305"
OPEN_SOURCE = {
    "T2V": ["AccVideo", "AnimateDiff", "Cogvideox1.5", "EasyAnimate", "HunyuanVideo", "IPOC", "LTX",
            "Open-Sora", "Pyramid-Flow", "RepVideo", "VideoCrafter", "Wan2.1"],
    "I2V": ["EasyAnimate", "LTX", "Pyramid-Flow", "SEINE", "SVD", "VideoCrafter"],
    "V2V": ["Cogvideox1.5", "LTX"],
}


def fetch(zip_path, ids, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    fs = HfFileSystem()
    with fs.open(f"datasets/{REPO}@{REV}/{zip_path}", "rb", block_size=2 ** 20) as f:
        zf = zipfile.ZipFile(f)
        have = {os.path.basename(i.filename): i for i in zf.infolist() if not i.is_dir()}
        got = 0
        for vid in ids:
            dst = os.path.join(out_dir, vid)
            if vid not in have or os.path.exists(dst):
                got += vid in have
                continue
            with zf.open(have[vid]) as src, open(dst + ".tmp", "wb") as o:
                o.write(src.read())
            os.replace(dst + ".tmp", dst)
            got += 1
    return zip_path, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20261021)
    a = ap.parse_args()
    split = hf_hub_download(REPO, "Split/test.jsonl", repo_type="dataset", revision=REV)
    ids = sorted(json.loads(l)["Video_id"] for l in open(split))
    ids = sorted(random.Random(a.seed).sample(ids, a.n))
    jobs = [("AIGVDBench/Real/Real.zip", os.path.join(a.out, "Real"))]
    jobs += [(f"AIGVDBench/OpenSource/{m}/{g}.zip", os.path.join(a.out, "Fake", f"{m}_{g}"))
             for m, gens in OPEN_SOURCE.items() for g in gens]
    with ThreadPoolExecutor(8) as ex:
        for z, got in ex.map(lambda j: fetch(j[0], ids, j[1]), jobs):
            print(f"  {got:4d}/{len(ids)}  {z}", flush=True)
    json.dump({"repo": REPO, "revision": REV, "seed": a.seed, "ids": ids},
              open(os.path.join(a.out, "sample.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
