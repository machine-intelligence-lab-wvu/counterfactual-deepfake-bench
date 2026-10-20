#!/usr/bin/env python
"""Frozen preprocessing views.

A view is a YAML spec in eval/views/<name>.yaml. `view_hash` is a hash of every other field,
including the pinned ffmpeg/x264 versions, so any change to the recipe or the toolchain is a
new view and can never be mixed with old scores.

  python -m eval.views.spec --freeze native face512   # fill ffmpeg_version + view_hash
  python -m eval.views.spec --check native face512    # verify hash and installed ffmpeg
"""
import argparse
import os
import subprocess

import yaml

from eval.common import FFMPEG, VIEW_DIR, canonical_hash


def path(name):
    return os.path.join(VIEW_DIR, f"{name}.yaml")


def compute_hash(spec):
    return canonical_hash({k: v for k, v in spec.items() if k != "view_hash"})


def installed_ffmpeg():
    out = subprocess.run([FFMPEG, "-version"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()[0].strip()


def load(name, check_toolchain=True):
    """Load a frozen view; refuse a spec whose hash or toolchain does not match."""
    with open(path(name)) as fh:
        spec = yaml.safe_load(fh)
    if spec.get("view_hash") != compute_hash(spec):
        raise SystemExit(f"view {name}: stored view_hash does not match its content "
                         "(a spec edit must be a new view name)")
    if check_toolchain and installed_ffmpeg() != spec["toolchain"]["ffmpeg_version"]:
        raise SystemExit(f"view {name}: installed ffmpeg {installed_ffmpeg()!r} != pinned "
                         f"{spec['toolchain']['ffmpeg_version']!r}")
    return spec


def freeze(name):
    with open(path(name)) as fh:
        spec = yaml.safe_load(fh)
    spec["toolchain"]["ffmpeg_version"] = installed_ffmpeg()
    spec["view_hash"] = compute_hash(spec)
    with open(path(name), "w") as fh:
        fh.write(f"# Frozen view spec. Do not edit: change = new view name. Hash: {spec['view_hash']}\n")
        yaml.safe_dump(spec, fh, sort_keys=False)
    return spec["view_hash"]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--freeze", nargs="+")
    g.add_argument("--check", nargs="+")
    a = ap.parse_args()
    for n in a.freeze or []:
        print(n, freeze(n))
    for n in a.check or []:
        print(n, load(n)["view_hash"], "ok")


if __name__ == "__main__":
    main()
