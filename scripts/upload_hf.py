#!/usr/bin/env python
"""Publish generated clips to the Hugging Face dataset repo.

Builds metadata.csv (one row per clip, flattened from the sidecar .json and,
when present, the QC report) at the dataset root, then uploads the folder.
Rows already in the hub's metadata.csv for clips not on this machine are kept,
so a cluster holding part of a dataset can append without erasing the rest
(--no-merge to rebuild from local clips only).
Either uploader only sends files the repo does not already hold, so this is
also how new runs get appended. huggingface_hub 2.x dropped the resumable
upload_large_folder, so fall back to upload_folder there.

  python scripts/upload_hf.py --data-root ../fairdeep-bench            # main run
  python scripts/upload_hf.py --data-root ../fairdeep-bench --include-pilots
  python scripts/upload_hf.py --metadata-only                          # just rebuild csv

Download elsewhere:
  hf download Ahsanz/fairdeep-bench --repo-type dataset --local-dir fairdeep-bench
"""
import argparse, csv, glob, json, os
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import EntryNotFoundError, RepositoryNotFoundError

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = ["synthetic"]
PILOTS = ["samples", "samples_motionfix", "seedtest", "setswap", "v2test", "v3test",
          "cleancombo"]
QC_COLS = ["motion_raw", "motion_norm", "luma_mean", "contrast", "black_frames",
           "stalled_frames", "pillarboxed", "letterboxed", "pass", "fail_reasons",
           "face_bg_people", "face_secondary_rel_max", "face_none_frames", "face_pass"]


def row(data_root, run, mp4):
    side = json.load(open(mp4[:-4] + ".json"))
    d, sc, g = side["demographic"], side["scene"], side.get("generation", {})
    return {
        "file_name": os.path.relpath(mp4, data_root),
        "run": run,
        "prompt_id": side["prompt_id"],
        "model": side["model"],
        "cell": side["cell"],
        "race": d["race"], "gender": d["gender"], "age_band": d["age_band"],
        "counterfactual_group": side["counterfactual_group"],
        "setting": sc["setting_key"], "lighting": sc["lighting_key"],
        "camera": side["camera"]["key"], "behavior": side["action"]["key"],
        "hair": side["appearance"]["hair"], "attire": side["appearance"]["attire"],
        "seed": side["seed"], "width": side["width"], "height": side["height"],
        "fps": side["fps"], "duration_s": side["duration_s"],
        "steps": g.get("steps"), "cfg": g.get("cfg"),
        "checkpoint": g.get("checkpoint"), "generated_utc": g.get("generated_utc"),
        "prompt_positive": side["prompt_rendered"]["positive"],
        "prompt_negative": side["prompt_rendered"]["negative"],
    }


def remote_rows(repo, local_names, columns):
    """Rows of the hub's metadata.csv for clips not in the local tree.

    A cluster usually holds only the clips it generated, so a metadata.csv built
    from its tree alone would drop every other row on upload.
    """
    try:
        path = hf_hub_download(repo, "metadata.csv", repo_type="dataset")
    except (EntryNotFoundError, RepositoryNotFoundError):
        return []
    remote = list(csv.DictReader(open(path)))
    if remote and list(remote[0]) != columns:
        raise SystemExit(f"{repo} metadata.csv columns differ from this script's; "
                         "rerun with --no-merge only if dropping hub rows is intended")
    return [r for r in remote if r["file_name"] not in local_names]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=os.path.join(os.path.dirname(HERE), "fairdeep-bench"))
    ap.add_argument("--repo", default="Ahsanz/fairdeep-bench")
    ap.add_argument("--qc", default=os.path.join(HERE, "manifests", "qc_report_*.csv"),
                    help="glob of qc/scan.py reports, merged by clip filename")
    ap.add_argument("--include-pilots", action="store_true")
    ap.add_argument("--public", action="store_true", help="create repo public (default private)")
    ap.add_argument("--metadata-only", action="store_true")
    ap.add_argument("--no-merge", action="store_true",
                    help="build metadata.csv from local clips only, dropping hub rows")
    args = ap.parse_args()
    root = os.path.abspath(args.data_root)
    runs = MAIN + (PILOTS if args.include_pilots else [])

    qc = {}
    for path in sorted(glob.glob(args.qc)):
        qc.update({r["clip"]: r for r in csv.DictReader(open(path))})

    rows = []
    for run in runs:
        for mp4 in sorted(glob.glob(os.path.join(root, run, "*", "*", "*.mp4"))):
            r = row(root, run, mp4)
            q = qc.get(os.path.basename(mp4)) if run == "synthetic" else None
            r.update({f"qc_{c}": (q or {}).get(c, "") for c in QC_COLS})
            rows.append(r)
    n_local = len(rows)
    if not args.no_merge:
        rows += remote_rows(args.repo, {r["file_name"] for r in rows}, list(rows[0]))
        rows.sort(key=lambda r: r["file_name"])
    with open(os.path.join(root, "metadata.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"metadata.csv: {len(rows)} clips ({n_local} local from {runs}, "
          f"{len(rows) - n_local} kept from {args.repo})")
    if args.metadata_only:
        return

    api = HfApi()
    api.create_repo(args.repo, repo_type="dataset", private=not args.public, exist_ok=True)
    allow = ["metadata.csv", "README.md"] + [f"{r}/**" for r in runs]
    large = getattr(api, "upload_large_folder", None)
    if large is not None:                      # huggingface_hub 1.x: resumable
        large(repo_id=args.repo, repo_type="dataset", folder_path=root,
              allow_patterns=allow)
    else:                                      # 2.x: one commit, same dedup
        api.upload_folder(repo_id=args.repo, repo_type="dataset", folder_path=root,
                          allow_patterns=allow,
                          commit_message="Add generated clips, sidecars and metadata")
    print(f"uploaded -> https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
