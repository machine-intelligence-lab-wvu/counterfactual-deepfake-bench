#!/usr/bin/env python
"""Shard id lists and "aggregate when complete", so one allocation can chain stages.

  python -m eval.finalize ids --view face512 --batch fake_b1 --shard 2 --nshards 4 > ids.txt
  python -m eval.finalize aggregate-if-complete --detector decof --views native face512

`ids` prints the render ids that `eval.preprocess --shard k --nshards n` handles, so the same
job can score exactly its own shard. `aggregate-if-complete` aggregates a view only when every
clip of every active batch has a final render record and every rendered clip is scored under
the current identity; a file lock makes concurrent jobs aggregate at most once, and a view whose
latest snapshot is newer than its newest score file is skipped.
"""
import argparse
import fcntl
import glob
import os
import subprocess
import sys

import pandas as pd

from eval.common import REPO, RESULTS, batch_info, eval_sets
from eval.detectors import registry
from eval.preprocess import latest_records, outputs_for
from eval.run import already_scored, read_scores
from eval.views.spec import load as load_view


def shard_ids(view, batch, shard, nshards):
    spec = load_view(view, check_toolchain=False)
    info = batch_info(batch)
    man = pd.read_csv(os.path.join(REPO, info["manifest"]), dtype={"clip_id": str})
    man = man.sort_values("clip_id").iloc[shard::nshards]
    return [o for row in man.to_dict("records") for o, _ in outputs_for(row, info["kind"], spec, "")]


def view_status(det, view):
    spec = load_view(view, check_toolchain=False)
    vh = spec["view_hash"]
    todo_render, todo_score = 0, 0
    for b in eval_sets()["active"]:
        info = batch_info(b)
        man = pd.read_csv(os.path.join(REPO, info["manifest"]), dtype={"clip_id": str})
        want = {o for row in man.to_dict("records") for o, _ in outputs_for(row, info["kind"], spec, "")}
        rec = latest_records(view, b, vh)
        final = set(rec.loc[rec["status"].isin(["ok", "excluded"]), "clip_id"]) if not rec.empty else set()
        todo_render += len(want - final)
        ok = set(rec.loc[rec["status"] == "ok", "clip_id"]) if not rec.empty else set()
        todo_score += len(ok - already_scored(read_scores(det.name, view, b), det, vh))
    return todo_render, todo_score


def snapshot_is_current(det, view):
    latest = os.path.join(RESULTS, "snapshots", det.name, view, "latest", "snapshot_meta.json")
    parts = glob.glob(os.path.join(RESULTS, "scores", det.name, view, "*", "part-*.parquet"))
    return os.path.exists(latest) and parts and os.path.getmtime(latest) > max(map(os.path.getmtime, parts))


def aggregate_if_complete(detector, views, extra):
    det = registry.get(detector)
    os.makedirs(os.path.join(RESULTS, "locks"), exist_ok=True)
    did = False
    for v in views:
        with open(os.path.join(RESULTS, "locks", f"aggregate-{detector}-{v}.lock"), "w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            r, s = view_status(det, v)
            if r or s:
                print(f"{detector}/{v}: not complete ({r} renders, {s} scores outstanding); skip")
                continue
            if snapshot_is_current(det, v):
                print(f"{detector}/{v}: latest snapshot already covers every score; skip")
                continue
            print(f"{detector}/{v}: complete, aggregating", flush=True)
            subprocess.run([sys.executable, "-m", "eval.aggregate", "--detector", detector,
                            "--view", v, *extra], check=True)
            did = True
    return did


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("ids")
    a1.add_argument("--view", required=True); a1.add_argument("--batch", required=True)
    a1.add_argument("--shard", type=int, required=True); a1.add_argument("--nshards", type=int, required=True)
    a2 = sub.add_parser("aggregate-if-complete")
    a2.add_argument("--detector", required=True); a2.add_argument("--views", nargs="+", required=True)
    a2.add_argument("--compare", action="store_true")
    a = ap.parse_args(sys.argv[1:2] + [x for x in sys.argv[2:] if x != "--"])
    if a.cmd == "ids":
        print("\n".join(shard_ids(a.view, a.batch, a.shard, a.nshards)))
    else:
        did = aggregate_if_complete(a.detector, a.views, [])
        if did and a.compare:
            subprocess.run([sys.executable, "-m", "eval.compare"], check=False)


if __name__ == "__main__":
    main()
