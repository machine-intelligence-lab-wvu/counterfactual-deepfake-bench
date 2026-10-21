"""Tests: manifest schema, view-hash stability, append-only/skip logic, metric functions on
hand-computed examples, aggregation over two batches. Run: python -m pytest eval/tests -q"""
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

from eval import metrics
from eval.common import REPO, canonical_hash
from eval.manifests.build_fake_manifest import REQUIRED, build, validate
from eval.views import spec as vspec

PY = sys.executable


# ------------------------------------------------------------------ manifest schema
def _metadata(tmp_path, n_groups=3, gens=("ltx23", "wan22")):
    rows = []
    for g in gens:
        for grp in range(n_groups):
            for race in ["black", "white"]:
                for gender in ["f", "m"]:
                    cell = f"{race}__{gender}__18-29"
                    rows.append({"file_name": f"synthetic/{g}/{race}_{gender}_18-29/{g}__{cell}__g{grp:03d}.mp4",
                                 "prompt_id": f"{g}__{cell}__g{grp:03d}", "model": g, "cell": cell,
                                 "race": race, "gender": gender, "age_band": "18-29",
                                 "counterfactual_group": str(grp), "setting": ["office", "lobby", "studio"][grp % 3],
                                 "lighting": ["harsh", "lowlight"][grp % 2], "behavior": "think",
                                 "camera": "static", "seed": "1", "width": "1280", "height": "704",
                                 "fps": "24", "duration_s": ["5.04", "6.04"][grp % 2],
                                 "qc_pass": "1", "qc_face_pass": "0" if (grp == 0 and race == "black" and gender == "m") else "1"})
    pd.DataFrame(rows).to_csv(tmp_path / "metadata.csv", index=False)
    return tmp_path


def test_manifest_schema(tmp_path):
    df = build(str(_metadata(tmp_path)), "fake_bt")
    assert validate(df)
    assert set(REQUIRED) <= set(df.columns)
    assert df["primary"].sum() == len(df) - 2          # one failing face-QC cell per generator
    assert set(df["duration_nominal"]) == {5, 6}
    bad = pd.concat([df, df.head(1)])
    with pytest.raises(ValueError, match="duplicate"):
        validate(bad)
    bad = df.copy(); bad.loc[0, "primary"] = 1 - bad.loc[0, "primary"]
    with pytest.raises(ValueError, match="primary"):
        validate(bad)


def test_committed_fake_b1_manifest_is_valid():
    p = os.path.join(REPO, "eval", "manifests", "fake_b1.csv")
    if not os.path.exists(p):
        pytest.skip("fake_b1.csv not built")
    df = pd.read_csv(p, dtype={"clip_id": str})
    assert validate(df)
    assert len(df) == 4536


# ------------------------------------------------------------------ views
def test_view_hash_stable_and_sensitive():
    for name in ["native", "face512"]:
        s = yaml.safe_load(open(vspec.path(name)))
        assert s["view_hash"] == vspec.compute_hash(s), f"{name}: stored hash stale"
        assert vspec.compute_hash(s) == vspec.compute_hash(dict(reversed(list(s.items()))))
        t = json.loads(json.dumps(s)); t["encode"]["crf"] = 24
        assert vspec.compute_hash(t) != s["view_hash"]
        t = json.loads(json.dumps(s)); t["toolchain"]["ffmpeg_version"] += "x"
        assert vspec.compute_hash(t) != s["view_hash"]


def test_view_load_refuses_edited_spec(tmp_path, monkeypatch):
    s = yaml.safe_load(open(vspec.path("native")))
    s["encode"]["crf"] = 18                       # edited without a new name/hash
    (tmp_path / "native.yaml").write_text(yaml.safe_dump(s))
    monkeypatch.setattr(vspec, "VIEW_DIR", str(tmp_path))
    with pytest.raises(SystemExit, match="does not match"):
        vspec.load("native", check_toolchain=False)


def test_face_window_shift_inward():
    from eval.preprocess import window
    # centred face: no long-axis shift; 1280x704 -> 931x512
    W2, H2, x0, y0, sx, sy = window(1280, 704, 640, 352, 512)
    assert (W2, H2) == (931, 512) and y0 == 0 and sx == 0 and sy == 0
    # face at the far left edge: window clamps to x0 = 0 and is counted as shifted
    W2, H2, x0, y0, sx, sy = window(1280, 704, 40, 352, 512)
    assert x0 == 0 and sx == round(40 * 931 / 1280 - 256) * -1
    # far right: clamps to W2 - 512
    _, _, x0, _, sx, _ = window(1280, 704, 1270, 352, 512)
    assert x0 == 931 - 512 and sx > 0


# ------------------------------------------------------------------ append-only / skip
class _Det:
    checkpoint_sha256, version = "abc", "1+x"


def test_already_scored_matches_identity_and_status():
    from eval.run import already_scored
    df = pd.DataFrame([
        {"clip_id": "a", "status": "ok", "checkpoint_sha256": "abc", "detector_version": "1+x", "view_hash": "v1"},
        {"clip_id": "b", "status": "failed", "checkpoint_sha256": "abc", "detector_version": "1+x", "view_hash": "v1"},
        {"clip_id": "c", "status": "ok", "checkpoint_sha256": "OTHER", "detector_version": "1+x", "view_hash": "v1"},
        {"clip_id": "d", "status": "ok", "checkpoint_sha256": "abc", "detector_version": "1+x", "view_hash": "v2"},
        {"clip_id": "e", "status": "ok", "checkpoint_sha256": "abc", "detector_version": "2+y", "view_hash": "v1"},
    ])
    assert already_scored(df, _Det(), "v1") == {"a"}      # failed retried; other identities rescored


def test_write_part_is_append_only(tmp_path, monkeypatch):
    import eval.run as run
    monkeypatch.setattr(run, "RESULTS", str(tmp_path))
    row = {c: "" for c in run.COLUMNS}; row.update(clip_id="a", score=0.5, status="ok")
    p1 = run.write_part([row], "d", "v", "b", 0, 0)
    p2 = run.write_part([row], "d", "v", "b", 0, 1)
    p3 = run.write_part([row], "d", "v", "b", 0, 1)   # same seq, later timestamp or same second
    assert p1 != p2 and os.path.exists(p1) and os.path.exists(p2)
    assert len(run.read_scores("d", "v", "b")) >= 2
    assert os.path.exists(p3)


# ------------------------------------------------------------------ metrics (hand-computed)
def test_gap_and_rates():
    assert metrics.gap([0.2, 0.5, 0.4]) == pytest.approx(0.3)
    assert np.isnan(metrics.gap([0.3]))
    assert metrics.detection_rate([0.1, 0.5, 0.7, 0.4], 0.5) == pytest.approx(0.5)
    reps = metrics.gap_reps(np.array([[0.1, 0.2], [0.4, np.nan], [0.3, 0.6]]))
    assert reps[0] == pytest.approx(0.3) and reps[1] == pytest.approx(0.4)


def test_cf_spread_and_flip():
    df = pd.DataFrame({"counterfactual_group": [1, 1, 2, 2, 2, 3],
                       "score": [0.0, 1.0, 0.6, 0.7, 0.8, 0.9]})
    s = metrics.cf_spread_per_group(df)
    assert s[1] == pytest.approx(0.5)                       # std([0,1], ddof=0)
    assert s[2] == pytest.approx(np.std([0.6, 0.7, 0.8]))
    assert 3 not in s.index                                 # single clip dropped
    f = metrics.flip_per_group(df, 0.5)
    assert f[1] == 1.0 and f[2] == 0.0 and 3 not in f.index


def test_group_bootstrap_resamples_whole_groups():
    gb = metrics.GroupBootstrap([10, 20, 30], B=50, seed=1)
    assert gb.W.shape == (50, 3) and (gb.W.sum(axis=1) == 3).all()
    vals, groups = np.array([1.0, 3.0, 5.0, 7.0]), np.array([10, 10, 20, 30])
    pt, reps = gb.mean(vals, groups)
    assert pt == pytest.approx(4.0)
    # replicate 0 by hand: each group's clips repeated W[0, g] times
    w = dict(zip(gb.groups, gb.W[0]))
    num = sum(w[g] * v for v, g in zip(vals, groups)); den = sum(w[g] for g in groups)
    assert reps[0] == pytest.approx(num / den)
    lo, hi = metrics.ci(reps)
    assert 1.0 <= lo <= pt <= hi <= 7.0
    # deterministic for a fixed seed
    assert np.array_equal(metrics.GroupBootstrap([10, 20, 30], B=50, seed=1).W, gb.W)


# ------------------------------------------------------------------ aggregation over 2 batches
def _setup_two_batches(tmp_path):
    from eval.detectors import registry
    det = registry.get("decof")
    view = yaml.safe_load(open(vspec.path("face512")))
    res = tmp_path / "results"; man_dir = tmp_path / "manifests"; man_dir.mkdir()
    rng = np.random.default_rng(0)
    batches = {}
    for b, gens in [("fake_bt1", ("ltx23", "wan22")), ("fake_bt2", ("hunyuan15",))]:
        md = _metadata(tmp_path / b if (tmp_path / b).mkdir() is None else tmp_path / b, n_groups=6, gens=gens)
        m = build(str(md), b)
        m.to_csv(man_dir / f"{b}.csv", index=False)
        batches[b] = {"kind": "fake", "manifest": str(man_dir / f"{b}.csv"), "data_root": str(md)}
        pre = pd.DataFrame({"clip_id": m["clip_id"], "source_clip_id": m["clip_id"], "batch": b,
                            "view": "face512", "view_hash": view["view_hash"], "status": "ok",
                            "error": "", "out_path": "/nonexistent.mp4", "shifted_x": 0,
                            "shift_x_px": 0, "shifted_y": 1, "timestamp": "2026-10-20T00:00:00Z"})
        d = res / "preprocess" / "face512" / b; d.mkdir(parents=True)
        pre.to_parquet(d / "part-0.parquet")
        sc = pd.DataFrame({"clip_id": m["clip_id"], "batch": b,
                           "score": rng.uniform(0, 1, len(m)), "status": "ok", "error": "",
                           "detector": det.name, "detector_version": det.version,
                           "checkpoint_sha256": det.checkpoint_sha256, "view": "face512",
                           "view_hash": view["view_hash"], "git_commit": "t", "gpu": "t",
                           "timestamp": "2026-10-20T00:00:01Z"})
        d = res / "scores" / "decof" / "face512" / b; d.mkdir(parents=True)
        sc.to_parquet(d / "part-0.parquet")
    sets = tmp_path / "eval_sets.yaml"
    sets.write_text(yaml.safe_dump({"active": list(batches), "batches": batches}))
    env = {**os.environ, "FAIRDEEP_RESULTS": str(res), "FAIRDEEP_EVAL_SETS": str(sets),
           "PYTHONPATH": REPO}
    return env, res, det, view


def _aggregate(env, *extra):
    return subprocess.run([PY, "-m", "eval.aggregate", "--detector", "decof", "--view", "face512",
                           "--B", "50", *extra], cwd=REPO, env=env, capture_output=True, text=True)


def test_aggregate_unions_batches_and_refuses_mixed_identity(tmp_path):
    env, res, det, view = _setup_two_batches(tmp_path)
    r = _aggregate(env, "--no-figures")
    assert r.returncode == 0, r.stderr[-2000:]
    latest = res / "snapshots" / "decof" / "face512" / "latest"
    meta = json.loads((latest / "snapshot_meta.json").read_text())
    assert meta["batches"] == ["fake_bt1", "fake_bt2"]
    assert meta["n_scored"] == 72 and meta["n_included_fakes"] == 72 - 3   # 3 face-QC fails
    sb = pd.read_csv(latest / "tables" / "score_by_breakdown.csv")
    assert set(sb["generator"]) == {"ltx23", "wan22", "hunyuan15", "all"}
    assert (latest / "REPORT.md").exists() and "pending" in (latest / "tables" / "pending_metrics.csv").read_text()
    used = pd.read_csv(latest / "manifest_used.csv")
    assert len(used) == 72 and used["included"].sum() == 69
    # a row from another checkpoint must make aggregate refuse
    d = res / "scores" / "decof" / "face512" / "fake_bt2"
    bad = pd.read_parquet(d / "part-0.parquet").head(1).assign(checkpoint_sha256="deadbeef")
    bad.to_parquet(d / "part-1.parquet")
    r = _aggregate(env, "--no-figures")
    assert r.returncode != 0 and "refusing to mix" in (r.stderr + r.stdout)
    r = _aggregate(env, "--no-figures", "--allow-other-identities")
    assert r.returncode == 0, r.stderr[-2000:]


def test_metric_words():
    """Dataset/benchmark framing: code, configs and reports avoid the two excluded words."""
    bad = []
    for root, _, files in os.walk(os.path.join(REPO, "eval")):
        for f in files:
            if f.endswith((".py", ".md", ".yaml", ".sh", ".csv")) and f != "test_pipeline.py":
                txt = open(os.path.join(root, f), errors="ignore").read().lower()
                for w in ("bias", "fairness"):
                    if w in txt:
                        bad.append(f"{f}: {w}")
    assert not bad, bad


def test_aggregate_folds_in_a_real_batch(tmp_path):
    """A scored real batch (two fps renders per clip) joins without rescoring the fakes."""
    env, res, det, view = _setup_two_batches(tmp_path)
    sets = yaml.safe_load(open(env["FAIRDEEP_EVAL_SETS"]))
    tpl = pd.read_csv(os.path.join(REPO, "eval", "manifests", "real_b1.template.csv"))
    reals = pd.concat([tpl.assign(clip_id=f"celebvhq__r{i}", source_id=f"r{i}") for i in range(5)])
    reals["batch"] = "real_bt"
    p = tmp_path / "manifests" / "real_bt.csv"; reals.to_csv(p, index=False)
    sets["batches"]["real_bt"] = {"kind": "real", "manifest": str(p), "data_root": "x"}
    sets["active"].append("real_bt")
    open(env["FAIRDEEP_EVAL_SETS"], "w").write(yaml.safe_dump(sets))
    ids = [f"{c}__fps{f}" for c in reals["clip_id"] for f in (24, 16)]
    d = res / "preprocess" / "face512" / "real_bt"; d.mkdir(parents=True)
    pd.DataFrame({"clip_id": ids, "source_clip_id": [i.rsplit("__fps", 1)[0] for i in ids],
                  "batch": "real_bt", "view": "face512", "view_hash": view["view_hash"],
                  "status": "ok", "error": "", "out_path": "/nonexistent.mp4", "shifted_x": 0,
                  "shift_x_px": 0, "shifted_y": 1, "timestamp": "2026-10-20T00:00:00Z"}
                 ).to_parquet(d / "part-0.parquet")
    d = res / "scores" / "decof" / "face512" / "real_bt"; d.mkdir(parents=True)
    pd.DataFrame({"clip_id": ids, "batch": "real_bt", "score": 0.1, "status": "ok", "error": "",
                  "detector": det.name, "detector_version": det.version,
                  "checkpoint_sha256": det.checkpoint_sha256, "view": "face512",
                  "view_hash": view["view_hash"], "git_commit": "t", "gpu": "t",
                  "timestamp": "2026-10-20T00:00:01Z"}).to_parquet(d / "part-0.parquet")
    r = _aggregate(env, "--no-figures")
    assert r.returncode == 0, r.stderr[-2000:]
    meta = json.loads((res / "snapshots" / "decof" / "face512" / "latest" / "snapshot_meta.json").read_text())
    assert meta["n_reals"] == 10 and meta["n_included_fakes"] == 69
    used = pd.read_csv(res / "snapshots" / "decof" / "face512" / "latest" / "manifest_used.csv")
    assert (used[used["kind"] == "real"]["render_status"] == "ok").all()


def test_realfake_metrics():
    """Weighted Mann-Whitney AUC equals sklearn's with unit weights; replicates are AUCs;
    the calibrated threshold flags 5% of reals; ties count one half."""
    from sklearn.metrics import roc_auc_score
    from eval.realfake import auc_reps, calibrated_threshold, tpr_at_fpr
    rng = np.random.default_rng(0)
    f, r = rng.normal(1, 1, 300), rng.normal(0, 1, 400)
    ones_f, ones_r = np.ones((3, 300)), np.ones((3, 400))
    pt, reps = auc_reps(f, r, ones_f, ones_r)
    ref = roc_auc_score(np.r_[np.ones(300), np.zeros(400)], np.r_[f, r])
    assert abs(pt - ref) < 1e-6 and np.allclose(reps, ref, atol=1e-5)
    # duplicating every fake and real (integer weights 2) leaves the AUC unchanged
    _, reps2 = auc_reps(f, r, 2 * ones_f, 2 * ones_r)
    assert np.allclose(reps2, ref, atol=1e-5)
    t = calibrated_threshold(r)
    assert abs((r >= t).mean() - 0.05) < 0.005
    tpr, t2 = tpr_at_fpr(f, r)
    assert t2 == t and 0 < tpr < 1
    pt_tie, _ = auc_reps(np.array([0.5]), np.array([0.5]), np.ones((1, 1)), np.ones((1, 1)))
    assert pt_tie == 0.5
