#!/usr/bin/env python
"""Score one batch in one view with one detector. Append-only, resumable.

  python -m eval.run --detector decof --view face512 --batch fake_b1 [--shard 0 --nshards 4]

Inputs are the preprocessed view videos recorded ok by eval.preprocess. Clips already scored
ok with the same (checkpoint_sha256, view_hash, detector_version) are skipped; failed clips
are retried. Results go to new part files under results/scores/<detector>/<view>/<batch>/,
never overwriting earlier ones.
"""
import argparse
import glob
import os
import time
import traceback

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from eval.common import REPO, RESULTS, batch_info, git_commit, gpu_name, utc_now
from eval.detectors import registry
from eval.preprocess import latest_records
from eval.views.spec import load as load_view

COLUMNS = ["clip_id", "batch", "score", "status", "error", "detector", "detector_version",
           "checkpoint_sha256", "view", "view_hash", "git_commit", "gpu", "timestamp"]


def scores_dir(detector, view, batch):
    return os.path.join(RESULTS, "scores", detector, view, batch)


def read_scores(detector, view, batch=None):
    pat = os.path.join(RESULTS, "scores", detector, view, batch or "*", "part-*.parquet")
    parts = sorted(glob.glob(pat))
    if not parts:
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)


def already_scored(df, det, view_hash):
    """clip_ids scored ok under exactly this detector identity and view hash."""
    if df.empty:
        return set()
    m = ((df["status"] == "ok") & (df["checkpoint_sha256"] == det.checkpoint_sha256)
         & (df["detector_version"] == det.version) & (df["view_hash"] == view_hash))
    return set(df.loc[m, "clip_id"])


class Clips(Dataset):
    def __init__(self, items, det):
        self.items, self.det = items, det

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        cid, path = self.items[i]
        try:
            return cid, self.det.prepare(path), ""
        except Exception as e:
            return cid, None, f"prepare: {type(e).__name__}: {e}"[:600]


def collate(batch):
    ok = [b for b in batch if b[1] is not None]
    bad = [(b[0], b[2]) for b in batch if b[1] is None]
    x = torch.stack([b[1] for b in ok]) if ok else None
    return [b[0] for b in ok], x, bad


def write_part(rows, detector, view, batch, shard, seq):
    d = scores_dir(detector, view, batch)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"part-{utc_now().replace(':', '')}-{os.environ.get('SLURM_JOB_ID', 'local')}"
                        f"-s{shard}-{seq:03d}.parquet")
    pd.DataFrame(rows, columns=COLUMNS).to_parquet(p, index=False)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detector", required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--shard", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_ID", 0)))
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--flush-every", type=int, default=1024, help="clips per part file")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only-ids", default=None)
    a = ap.parse_args()

    det = registry.get(a.detector)
    spec = load_view(a.view, check_toolchain=False)
    batch_info(a.batch)
    pre = latest_records(a.view, a.batch, spec["view_hash"])
    if pre.empty:
        raise SystemExit(f"no preprocess records for {a.view}/{a.batch}; run eval.preprocess first")
    pre = pre[pre["status"] == "ok"].sort_values("clip_id")
    if a.only_ids:
        keep = set(open(a.only_ids).read().split())
        pre = pre[pre["clip_id"].isin(keep)]
    pre = pre.iloc[a.shard::a.nshards]
    done = already_scored(read_scores(a.detector, a.view, a.batch), det, spec["view_hash"])
    items = [(c, p) for c, p in zip(pre["clip_id"], pre["out_path"]) if c not in done]
    if a.limit:
        items = items[:a.limit]
    print(f"{a.detector}/{a.view}/{a.batch} shard {a.shard}/{a.nshards}: {len(items)} to score, "
          f"{len(done)} already scored", flush=True)
    if not items:
        return

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    det.load(dev)
    base = {**det.identity(), "batch": a.batch, "view": a.view, "view_hash": spec["view_hash"],
            "git_commit": git_commit(), "gpu": gpu_name()}
    dl = DataLoader(Clips(items, det), batch_size=a.batch_size, num_workers=a.workers,
                    collate_fn=collate, pin_memory=True, persistent_workers=False,
                    prefetch_factor=4 if a.workers else None)
    rows, seq, n, t0 = [], 0, 0, time.time()
    for ids, x, bad in dl:
        now = utc_now()
        for cid, err in bad:
            rows.append({**base, "clip_id": cid, "score": float("nan"), "status": "failed",
                         "error": err, "timestamp": now})
        if ids:
            try:
                s = det.score(x).tolist()
                rows += [{**base, "clip_id": c, "score": float(v), "status": "ok", "error": "",
                          "timestamp": now} for c, v in zip(ids, s)]
            except Exception as e:
                traceback.print_exc()
                rows += [{**base, "clip_id": c, "score": float("nan"), "status": "failed",
                          "error": f"score: {type(e).__name__}: {e}"[:600], "timestamp": now}
                         for c in ids]
        n += len(ids) + len(bad)
        if len(rows) >= a.flush_every:
            write_part(rows, a.detector, a.view, a.batch, a.shard, seq); seq += 1; rows = []
        if n % (a.batch_size * 10) < a.batch_size:
            print(f"  {n}/{len(items)} {n / (time.time() - t0):.1f} clips/s", flush=True)
    if rows:
        write_part(rows, a.detector, a.view, a.batch, a.shard, seq)
    dt = time.time() - t0
    print(f"done {n} clips in {dt:.0f}s ({n / dt:.2f} clips/s) on {base['gpu']}")
    try:
        from eval.coverage import write_coverage
        write_coverage()
    except Exception as e:
        print(f"coverage not updated: {e}")


if __name__ == "__main__":
    main()
