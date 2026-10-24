"""Pull only the REAL clips out of DFDC train-part zips.

Each `dfdc_train_part_N.zip` carries ~2,300 mp4s and one `metadata.json`:

    {"aaqaifqrwn.mp4": {"label": "FAKE", "split": "train", "original": "xyz.mp4"},
     "abarnvbtwb.mp4": {"label": "REAL", "split": "train"}, ...}

Only `label == "REAL"` is pristine camera footage; everything else is a face
swap built *from* those reals. For the real half of the benchmark we want the
REAL rows and nothing else - roughly a fifth of each part - so this extracts
selectively instead of unpacking ~10 GB per part to then delete 80% of it.

Reading the zip's central directory needs the whole file, so run this only on
completed downloads.

    python extract_dfdc.py --zips "<dir>/*.zip" --out <dir>/real_raw
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import zipfile
from pathlib import Path


def part_name(zf: zipfile.ZipFile, fallback: str) -> str:
    for n in zf.namelist():
        head = n.split("/")[0]
        if head.startswith("dfdc_train_part"):
            return head
    return fallback


def find_metadata(zf: zipfile.ZipFile) -> str | None:
    for n in zf.namelist():
        if os.path.basename(n) == "metadata.json":
            return n
    return None


def process_zip(path: Path, out_root: Path, dry: bool) -> dict:
    with zipfile.ZipFile(path) as zf:
        part = part_name(zf, path.stem)
        meta_name = find_metadata(zf)
        if meta_name is None:
            return {"zip": path.name, "error": "no metadata.json"}

        meta = json.loads(zf.read(meta_name))
        by_name = {os.path.basename(n): n for n in zf.namelist()
                   if n.lower().endswith(".mp4")}

        reals = [k for k, v in meta.items() if str(v.get("label", "")).upper() == "REAL"]
        fakes = len(meta) - len(reals)

        out_dir = out_root / part
        out_dir.mkdir(parents=True, exist_ok=True)

        written, missing = 0, []
        for name in sorted(reals):
            member = by_name.get(name)
            if member is None:
                missing.append(name)
                continue
            dest = out_dir / name
            if dest.exists() and dest.stat().st_size > 0:
                written += 1
                continue
            if dry:
                written += 1
                continue
            with zf.open(member) as src, open(dest, "wb") as fh:
                while True:
                    buf = src.read(1 << 20)
                    if not buf:
                        break
                    fh.write(buf)
            written += 1

        # The REAL rows are the only ones we keep, but the FAKE rows record which
        # real each fake was derived from; keep the whole metadata so that link
        # survives for anyone who later wants the matched pairs.
        if not dry:
            (out_root / f"{part}_metadata.json").write_text(json.dumps(meta, indent=1))

        return {"zip": path.name, "part": part, "n_entries": len(meta),
                "n_real": len(reals), "n_fake": fakes, "written": written,
                "missing": len(missing)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", required=True, help="glob for the DFDC part zips")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    zips = sorted(Path(p) for p in glob.glob(a.zips))
    if not zips:
        print(f"no zips matched {a.zips}", file=sys.stderr)
        return 1
    out_root = Path(a.out)
    out_root.mkdir(parents=True, exist_ok=True)

    total_real = 0
    for z in zips:
        if not zipfile.is_zipfile(z):
            print(f"  {z.name}: not a complete zip (still downloading?) - skipped")
            continue
        r = process_zip(z, out_root, a.dry_run)
        if "error" in r:
            print(f"  {z.name}: {r['error']}")
            continue
        total_real += r["written"]
        print(f"  {r['part']}: {r['n_entries']} clips, {r['n_real']} REAL / "
              f"{r['n_fake']} FAKE -> extracted {r['written']}"
              + (f" ({r['missing']} listed but absent)" if r["missing"] else ""))
    print(f"\ntotal REAL clips: {total_real} -> {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
