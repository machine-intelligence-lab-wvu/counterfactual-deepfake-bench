"""Shared paths, hashing and small helpers for the evaluation pipeline.

Data lives outside the repo (videos, weights, score parquet); code, configs, manifests and
snapshots live in it. Every location can be overridden by environment variable so another
cluster only edits eval/env.sh.
"""
import datetime as _dt
import hashlib
import json
import os
import subprocess

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(REPO, "eval")
RESULTS = os.environ.get("FAIRDEEP_RESULTS", os.path.join(REPO, "results"))
VIEWS_ROOT = os.environ.get("FAIRDEEP_VIEWS_ROOT", "/work/nvme/bjej/rahamed/fairdeep/eval_views")
WEIGHTS = os.environ.get("FAIRDEEP_WEIGHTS", "/work/nvme/bjej/rahamed/fairdeep/eval_ext/weights")
EXT = os.environ.get("FAIRDEEP_EXT", "/work/nvme/bjej/rahamed/fairdeep/eval_ext")
FFMPEG = os.environ.get("FAIRDEEP_FFMPEG", "/projects/bjej/rahamed/fairdeep_eval/ffmpeg/bin/ffmpeg")
FFPROBE = os.environ.get("FAIRDEEP_FFPROBE", os.path.join(os.path.dirname(FFMPEG), "ffprobe"))

MANIFEST_DIR = os.path.join(EVAL, "manifests")
VIEW_DIR = os.path.join(EVAL, "views")


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def canonical_hash(obj, n=16):
    """Stable hash of a JSON-able object: sorted keys, no whitespace."""
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(s.encode()).hexdigest()[:n]


def git_commit():
    try:
        out = subprocess.run(["git", "-C", REPO, "rev-parse", "--short=12", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def utc_now():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M")


def load_yaml(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def eval_sets():
    return load_yaml(os.environ.get("FAIRDEEP_EVAL_SETS",
                                    os.path.join(MANIFEST_DIR, "eval_sets.yaml")))


def batch_info(batch):
    sets = eval_sets()
    if batch not in sets["batches"]:
        raise SystemExit(f"unknown batch {batch!r}; known: {sorted(sets['batches'])}")
    return sets["batches"][batch]


def gpu_name():
    try:
        import torch
        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
    except Exception:
        return "unknown"
