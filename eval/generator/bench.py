#!/usr/bin/env python
"""Generator benchmark, Track A (EVALUATION_PLAN.md section 6.4). Detector-independent.

  python -m eval.generator.bench measure   [--batches fake_b1 fake_b2] [--workers 24]   # GPU
  python -m eval.generator.bench aggregate [--B 1000]                                   # CPU

measure: per generated clip, 8 face crops spread over the clip (YuNet, 0.35 margin) labelled
by FairFace (res34, 7-race) exactly as the real half is labelled, plus face sharpness
(variance of the Laplacian on each crop resized to 224x224, median over crops; resizing
removes the face-size dependence). Append-only per (clip, FairFace checkpoint, version):
  results/generator/measures/<batch>/part-*.parquet

aggregate: unions every active fake batch and writes a timestamped snapshot:
  results/snapshots/generator/<YYYYMMDD-HHMM>/  tables/*.csv figures/* REPORT.md meta.json
with
  - QC acceptance (technical, face, primary) over every generated clip;
  - demographic fidelity over primary clips: perceived (FairFace) vs requested race, gender,
    age band and the full cell. A FairFace 40-49 clip matches either 30-44 or 45-59, since
    that band straddles the taxonomy's 44/45 cut. Clips with no detected face are reported,
    not counted as mismatches;
  - confusion of requested vs perceived race and age band, per generator;
  - motion (QC motion, normalised) and visual quality proxies: face sharpness, mean luma,
    contrast. These are no-reference proxies, not a perceptual quality score.
Every breakdown (generator x race, gender, age band, 56 cells, scene factors) carries a 95%
interval from the shared counterfactual-group bootstrap of aggregate.py.
"""
import argparse
import glob
import json
import os
import socket
import sys
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd

from eval.common import (REPO, RESULTS, WEIGHTS, batch_info, eval_sets, git_commit,
                         sha256_file, stamp, utc_now)

VERSION = "1"
N_CROPS = 8
CROP_MARGIN = 0.35
FF_WEIGHTS = os.path.join(WEIGHTS, "fairface", "res34_fair_align_multi_7_20190809.pt")
FF_SHA = "37f2e74c0e7da196f8edd7dae0c88cffdbef7923beebebcc27381f0ad0fdb2c1"
YUNET = os.path.join(WEIGHTS, "yunet", "face_detection_yunet_2023mar.onnx")
MEASURE_DIR = os.path.join(RESULTS, "generator", "measures")


# ------------------------------------------------------------------ measure (CPU part)
def crops_and_sharpness(path):
    import cv2
    cv2.setNumThreads(1)
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return path, [], np.nan, "unreadable"
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if total <= 0:
        cap.release()
        return path, [], np.nan, "no frames"
    det = cv2.FaceDetectorYN.create(YUNET, "", (w, h), 0.6, 0.3, 5000)
    want = set(np.linspace(0, total - 1, min(N_CROPS, total)).round().astype(int).tolist())
    crops, sharp, i = [], [], 0
    while i <= max(want):
        ok, frame = cap.read()
        if not ok:
            break
        if i in want:
            _, faces = det.detect(frame)
            if faces is not None and len(faces):
                f = max(faces, key=lambda r: r[3])
                x, y, bw, bh = f[0], f[1], f[2], f[3]
                mx, my = bw * CROP_MARGIN, bh * CROP_MARGIN
                x0, y0 = int(max(0, x - mx)), int(max(0, y - my))
                x1, y1 = int(min(w, x + bw + mx)), int(min(h, y + bh + my))
                if x1 > x0 and y1 > y0:
                    c = frame[y0:y1, x0:x1]
                    crops.append(c)
                    g = cv2.cvtColor(cv2.resize(c, (224, 224), interpolation=cv2.INTER_AREA),
                                     cv2.COLOR_BGR2GRAY)
                    sharp.append(float(cv2.Laplacian(g, cv2.CV_64F).var()))
        i += 1
    cap.release()
    return path, crops, (float(np.median(sharp)) if sharp else np.nan), ""


def done_ids(batch):
    parts = glob.glob(os.path.join(MEASURE_DIR, batch, "*.parquet"))
    if not parts:
        return set()
    d = pd.concat([pd.read_parquet(p) for p in parts])
    d = d[(d["fairface_sha256"] == FF_SHA) & (d["version"] == VERSION) & (d["status"] == "ok")]
    return set(d["clip_id"])


def measure(a):
    import torch
    from eval.generator.fairface import FairFace
    if sha256_file(FF_WEIGHTS) != FF_SHA:
        raise SystemExit(f"checksum mismatch: {FF_WEIGHTS}")
    ff = FairFace(FF_WEIGHTS, device="cuda" if torch.cuda.is_available() else "cpu")
    batches = a.batches or [b for b in eval_sets()["active"] if batch_info(b)["kind"] == "fake"]
    for b in batches:
        man = pd.read_csv(os.path.join(REPO, batch_info(b)["manifest"]), dtype={"clip_id": str})
        todo = man[~man["clip_id"].isin(done_ids(b))]
        print(f"{b}: {len(todo)} of {len(man)} clips to measure on {ff.device}", flush=True)
        if todo.empty:
            continue
        out = os.path.join(MEASURE_DIR, b)
        os.makedirs(out, exist_ok=True)
        by_path = dict(zip(todo["path"], todo["clip_id"]))
        rows, part = [], 0
        with Pool(a.workers) as pool:
            for k, (path, crops, sharp, err) in enumerate(
                    pool.imap_unordered(crops_and_sharpness, list(by_path), chunksize=4), 1):
                res = ff.predict_clip(crops) if crops else {"ok": False}
                rows.append({
                    "clip_id": by_path[path], "batch": b, "status": "ok" if not err else "failed",
                    "error": err, "n_face_crops": len(crops), "face_found": int(bool(crops)),
                    "face_sharpness": sharp,
                    "perceived_race": res.get("race"), "perceived_gender": res.get("gender"),
                    "perceived_age_band": res.get("age_band"),
                    "fairface_age": res.get("fairface_age"),
                    "age_ambiguous": res.get("age_ambiguous"), "age_band_alt": res.get("age_band_alt"),
                    "race_conf": res.get("fairface_race_conf"),
                    "gender_conf": res.get("fairface_gender_conf"),
                    "age_conf": res.get("fairface_age_conf"),
                    "race_probs": json.dumps(res.get("race_probs")) if res.get("ok") else "",
                    "age_probs": json.dumps(res.get("age_probs")) if res.get("ok") else "",
                    "fairface_sha256": FF_SHA, "version": VERSION, "git_commit": git_commit(),
                    "timestamp": utc_now()})
                if len(rows) >= 500 or k == len(by_path):
                    pd.DataFrame(rows).to_parquet(os.path.join(
                        out, f"part-{stamp()}-{os.getpid()}-{part:03d}.parquet"), index=False)
                    rows, part = [], part + 1
                if k % 250 == 0 or k == len(by_path):
                    print(f"  {k}/{len(by_path)}", flush=True)


# ------------------------------------------------------------------ aggregate
def load(batches):
    man = pd.concat([pd.read_csv(os.path.join(REPO, batch_info(b)["manifest"]),
                                 dtype={"clip_id": str}) for b in batches], ignore_index=True)
    parts = [p for b in batches for p in glob.glob(os.path.join(MEASURE_DIR, b, "*.parquet"))]
    if not parts:
        raise SystemExit("no measures; run `measure` first")
    m = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    m = m[(m["fairface_sha256"] == FF_SHA) & (m["version"] == VERSION)]
    m = m.sort_values("timestamp").groupby("clip_id", as_index=False).tail(1)
    df = man.merge(m.drop(columns=["batch"]), on="clip_id", how="left")
    df["measured"] = df["status"].eq("ok").astype(int)
    for k in ["race", "gender", "age_band"]:
        df[k] = df[k].astype(str)
    has = df["face_found"].eq(1)
    df["race_match"] = np.where(has, (df["perceived_race"] == df["race"]).astype(float), np.nan)
    df["gender_match"] = np.where(has, (df["perceived_gender"] == df["gender"]).astype(float), np.nan)
    age_ok = (df["perceived_age_band"] == df["age_band"]) | (
        df["age_ambiguous"].eq(1) & (df["age_band_alt"] == df["age_band"]))
    df["age_match"] = np.where(has, age_ok.astype(float), np.nan)
    df["cell_match"] = np.where(has, (df["race_match"] * df["gender_match"] * df["age_match"]), np.nan)
    df["no_face"] = np.where(df["measured"] == 1, 1 - df["face_found"].fillna(0), np.nan)
    return df


def confusion(df, req, per):
    rows = []
    for gen, d in df[df["face_found"] == 1].groupby("generator"):
        ct = pd.crosstab(d[req], d[per])
        share = ct.div(ct.sum(axis=1), axis=0)
        for r in ct.index:
            for p in ct.columns:
                rows.append({"generator": gen, "requested": r, "perceived": p,
                             "n": int(ct.loc[r, p]), "share_of_requested": float(share.loc[r, p])})
    return pd.DataFrame(rows)


def aggregate(a):
    from eval.aggregate import breakdown_table, gap_table
    from eval.metrics import B_DEFAULT, SEED, GroupBootstrap
    batches = [b for b in eval_sets()["active"] if batch_info(b)["kind"] == "fake"]
    df = load(batches)
    gb = GroupBootstrap(df["counterfactual_group"], B=a.B or B_DEFAULT, seed=SEED)
    prim = df[(df["primary"] == 1) & (df["measured"] == 1)].copy()
    snap = os.path.join(RESULTS, "snapshots", "generator", stamp())
    tdir, fdir = os.path.join(snap, "tables"), os.path.join(snap, "figures")
    os.makedirs(tdir, exist_ok=True); os.makedirs(fdir, exist_ok=True)
    T = {}
    T["inclusion"] = df.groupby(["batch", "generator"]).agg(
        clips=("clip_id", "size"), qc_technical=("qc_technical", "sum"), qc_face=("qc_face", "sum"),
        primary=("primary", "sum"), measured=("measured", "sum"),
        face_found=("face_found", "sum")).reset_index()
    for col in ["qc_technical", "qc_face", "primary"]:          # over every generated clip
        T[f"qc_acceptance_{col}"] = breakdown_table(df.assign(**{col: df[col].astype(float)}), gb, col)
    T["qc_acceptance_primary_gap"] = gap_table(df.assign(primary=df["primary"].astype(float)), gb, "primary")
    fid = prim[prim["face_found"] == 1]
    for col in ["race_match", "gender_match", "age_match", "cell_match"]:
        T[f"fidelity_{col}"] = breakdown_table(fid, gb, col)
    T["fidelity_cell_match_gap"] = gap_table(fid, gb, "cell_match")
    T["fidelity_no_face"] = breakdown_table(prim, gb, "no_face")
    T["confusion_race"] = confusion(prim, "race", "perceived_race")
    T["confusion_age_band"] = confusion(prim, "age_band", "perceived_age_band")
    T["confusion_gender"] = confusion(prim, "gender", "perceived_gender")
    for col in ["qc_motion_norm", "face_sharpness", "qc_luma_mean", "qc_contrast"]:
        d = prim[prim[col].notna()]
        T[f"quality_{col}"] = breakdown_table(d, gb, col)
        T[f"quality_{col}_gap"] = gap_table(d, gb, col)
    for k, v in T.items():
        if v is not None and not v.empty:
            v.to_csv(os.path.join(tdir, f"{k}.csv"), index=False, float_format="%.6g")

    figs = [] if a.no_figures else figures(T, fdir)
    meta = {"track": "A (generator benchmark)", "batches": batches, "n_clips": int(len(df)),
            "n_primary_measured": int(len(prim)), "n_face_found": int(len(fid)),
            "fairface_sha256": FF_SHA, "measure_version": VERSION,
            "bootstrap": {"B": gb.B, "seed": SEED, "unit": "counterfactual_group"},
            "git_commit": git_commit(), "created": utc_now(), "snapshot": os.path.basename(snap),
            "host": socket.gethostname()}
    with open(os.path.join(snap, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)
    report(snap, meta, T, figs)
    latest = os.path.join(os.path.dirname(snap), "latest")
    if os.path.lexists(latest + ".tmp"):
        os.remove(latest + ".tmp")
    os.symlink(os.path.basename(snap), latest + ".tmp")
    os.replace(latest + ".tmp", latest)
    print(f"snapshot {snap}: {len(df)} clips, {len(prim)} primary measured, {len(T)} tables, "
          f"{len(figs)} figures")


def figures(T, fdir):
    from eval import figures as F
    out = []
    F.cell_heatmap(T["qc_acceptance_primary"], fdir, out, "heatmap_qc_acceptance_cells",
                   "QC acceptance (technical and face): 56 cells x generator", "acceptance rate")
    F.cell_heatmap(T["fidelity_cell_match"], fdir, out, "heatmap_cell_fidelity",
                   "Perceived cell = requested cell (FairFace): 56 cells x generator", "match rate")
    for col, title in [("race_match", "race"), ("gender_match", "gender"), ("age_match", "age band"),
                       ("cell_match", "full cell")]:
        F.pointrange(T[f"fidelity_{col}"], ["race", "gender", "age_band"], fdir, out,
                     f"fidelity_{col}", f"Perceived {title} = requested, by requested subgroup, 95% CI",
                     "match rate")
    F.pointrange(T["quality_qc_motion_norm"], ["race", "gender", "age_band", "setting", "lighting"],
                 fdir, out, "quality_motion", "Motion (QC, normalised), 95% CI", "motion")
    F.pointrange(T["quality_face_sharpness"], ["race", "gender", "age_band", "setting", "lighting"],
                 fdir, out, "quality_face_sharpness", "Face sharpness (Laplacian variance at 224 px), 95% CI",
                 "sharpness")
    confusion_fig(T["confusion_race"], fdir, out, "confusion_race", "Requested vs perceived race")
    confusion_fig(T["confusion_age_band"], fdir, out, "confusion_age_band",
                  "Requested vs perceived age band")
    return out


def confusion_fig(table, fdir, out, name, title):
    from eval import figures as F
    plt = F._style()
    gens = [g for g in F.GEN_ORDER if g in set(table["generator"])]
    fig, axes = plt.subplots(1, len(gens), figsize=(4.2 * len(gens), 4.2), squeeze=False)
    for ax, g in zip(axes[0], gens):
        t = table[table["generator"] == g].pivot(index="requested", columns="perceived",
                                                 values="share_of_requested").fillna(0)
        cols = sorted(set(t.index) | set(t.columns))
        t = t.reindex(index=sorted(t.index), columns=cols, fill_value=0)
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list("seq", ["#ffffff"] + F.SEQ)
        ax.imshow(t.to_numpy(), cmap=cmap, vmin=0, vmax=1)
        for i in range(t.shape[0]):
            for j in range(t.shape[1]):
                v = t.iat[i, j]
                if v >= 0.005:
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                            color="white" if v > 0.55 else F.INK)
        ax.set_xticks(range(len(cols)), cols, rotation=60, ha="right", fontsize=8)
        ax.set_yticks(range(t.shape[0]), t.index, fontsize=8)
        ax.set_title(F.GEN_LABEL.get(g, g), loc="left")
        ax.set_xlabel("perceived (FairFace)"); ax.grid(False)
    axes[0, 0].set_ylabel("requested")
    fig.suptitle(f"{title} (row share)", x=0.01, ha="left")
    F._save(fig, fdir, name, out)


def report(snap, meta, T, figs):
    from eval.report import _md
    L = ["# Generator benchmark (Track A, section 6.4)\n",
         f"Snapshot `{meta['snapshot']}`, batches {', '.join(meta['batches'])}; "
         f"{meta['n_clips']} generated clips, {meta['n_primary_measured']} primary and measured, "
         f"{meta['n_face_found']} with a face found by YuNet. Intervals: 95%, {meta['bootstrap']['B']} "
         "resamples of whole counterfactual groups.\n",
         "Perceived labels come from FairFace (res34, 7-race) on 8 face crops per clip, the same "
         "procedure as the real half. They are perceived-presentation labels from a classifier "
         "with its own error profile (weaker on darker skin and older faces), so a low match rate "
         "mixes generator drift and classifier error; the reals carry the same classifier's labels.\n",
         "## Inclusion\n", _md(T["inclusion"], fmt="{:.0f}")]
    for col, name in [("qc_technical", "technical QC"), ("qc_face", "face QC"),
                      ("primary", "technical and face QC (primary)")]:
        t = T[f"qc_acceptance_{col}"]
        L.append(f"## QC acceptance: {name}\n")
        L.append(_md(t[t["factor"].isin(["overall", "race", "gender", "age_band"])],
                     ["generator", "factor", "level", "n", "estimate", "ci_lo", "ci_hi"]))
    L.append("### Acceptance gap (primary)\n")
    L.append(_md(T["qc_acceptance_primary_gap"], ["generator", "attribute", "gap", "ci_lo", "ci_hi",
                                                  "max_level", "min_level"]))
    for col, name in [("race_match", "race"), ("gender_match", "gender"), ("age_match", "age band"),
                      ("cell_match", "full cell")]:
        t = T[f"fidelity_{col}"]
        L.append(f"## Demographic fidelity: perceived {name} = requested\n")
        L.append(_md(t[t["factor"].isin(["overall", "race", "gender", "age_band"])],
                     ["generator", "factor", "level", "n", "estimate", "ci_lo", "ci_hi"]))
    L.append("### Cell-fidelity gap\n")
    L.append(_md(T["fidelity_cell_match_gap"], ["generator", "attribute", "gap", "ci_lo", "ci_hi",
                                                "max_level", "min_level"]))
    t = T["fidelity_no_face"]
    L.append("### No face found (primary clips)\n")
    L.append(_md(t[t["factor"] == "overall"], ["generator", "n", "estimate", "ci_lo", "ci_hi"]))
    for col, name in [("qc_motion_norm", "Motion (QC, normalised)"),
                      ("face_sharpness", "Face sharpness"), ("qc_luma_mean", "Mean luma"),
                      ("qc_contrast", "Contrast")]:
        t = T[f"quality_{col}"]
        L.append(f"## {name}\n")
        L.append(_md(t[t["factor"].isin(["overall", "race", "gender", "age_band"])],
                     ["generator", "factor", "level", "n", "estimate", "ci_lo", "ci_hi"]))
        L.append(_md(T[f"quality_{col}_gap"], ["generator", "attribute", "gap", "ci_lo", "ci_hi",
                                               "max_level", "min_level"]))
    L.append("## Figures\n")
    for f in figs:
        L.append(f"`figures/{f}.pdf`\n\n![{f}](figures/{f}.png)\n")
    L.append("Full tables, including 56-cell and scene-factor breakdowns: `tables/*.csv`.\n")
    with open(os.path.join(snap, "REPORT.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["measure", "aggregate"])
    ap.add_argument("--batches", nargs="*", default=None)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--B", type=int, default=None)
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args()
    measure(a) if a.stage == "measure" else aggregate(a)


if __name__ == "__main__":
    sys.exit(main())
