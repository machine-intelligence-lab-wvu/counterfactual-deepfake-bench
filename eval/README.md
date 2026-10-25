# Evaluation pipeline

Score once, aggregate any time (`EVALUATION_PLAN.md`). Every clip is scored once per
(detector, checkpoint, view); `aggregate` recomputes all metrics from everything scored so far
and writes a timestamped snapshot. Decisions, versions and checksums: `eval/LOG.md`.

```
eval/manifests/<batch>.csv      one row per clip + metadata + flags (qc_technical, qc_face, primary)
eval/manifests/eval_sets.yaml   which batches are active
eval/views/<view>.yaml          frozen preprocessing specs (+ view_hash, pinned ffmpeg)
eval/detectors/<name>/          one folder per detector, registered in eval/detectors/registry.py
results/preprocess/<view>/<batch>.csv           render record per clip (ok / excluded / failed)
results/scores/<detector>/<view>/<batch>/*.parquet   append-only scores (not committed)
results/snapshots/<detector>/<view>/<stamp>/   tables, figures, REPORT.md (committed); latest ->
results/compare/<stamp>/                       cross-detector tables and figures
results/coverage.md                            scored / pending / failed per batch x detector x view
```

Large data stays outside the repo: view videos in `$DFBENCH_VIEWS_ROOT`, weights and pinned
code checkouts in `$DFBENCH_EXT`. Paths are set in `eval/env.sh`.

## Every session

```bash
cd counterfactual-deepfake-bench
source eval/env.sh                 # PyTorch module 2.10.0 + venv + pinned ffmpeg + paths
python -m pytest eval/tests -q     # before every commit
```
Heavy work runs as Slurm jobs on `ghx4` (account `bjej-dtai-gh`; never `ghx4-interactive`).
Every job is resumable: resubmitting skips finished clips and retries failures.

## Add `fake_b2` (more generated clips)

1. **Data + manifest.** Download the clips with their `metadata.csv` (same columns as
   deepfake-bench-data), then
   ```bash
   python -m eval.manifests.build_fake_manifest --batch fake_b2 --data-root <dir with metadata.csv> --check-files
   ```
   In `eval/manifests/eval_sets.yaml` set `fake_b2.data_root` and add `fake_b2` to `active`.
2. **Preprocess both views** (4-way array per view):
   ```bash
   for v in native face512; do
     sbatch --array=0-3 --export=ALL,VIEW=$v,BATCH=fake_b2,NSHARDS=4 eval/slurm/preprocess.sbatch
   done
   ```
3. **Score**, after step 2 finishes:
   ```bash
   for v in native face512; do
     sbatch --export=ALL,DETECTOR=decof,VIEW=$v,BATCH=fake_b2 eval/slurm/score.sbatch
   done
   ```
4. **Aggregate** (uses fake_b1 + fake_b2; nothing from fake_b1 is re-scored):
   ```bash
   sbatch --export=ALL,DETECTOR=decof,VIEWS="native face512" eval/slurm/aggregate.sbatch
   python -m eval.compare
   ```
   Commit `eval/manifests/fake_b2.csv`, `eval/manifests/eval_sets.yaml`,
   `results/preprocess/*/fake_b2.csv`, `results/coverage.md` and the new snapshots.

## Add `real_b1` (CelebV-HQ reals)

1. **Manifest.** Fill `eval/manifests/real_b1.template.csv` (one row per real clip) and save it
   as `eval/manifests/real_b1.csv`:

   | column | meaning |
   |---|---|
   | clip_id | unique id (e.g. `celebvhq__<source_id>`) |
   | batch, label | `real_b1`, `0` |
   | source_id, path | CelebV-HQ id, absolute path to the source video |
   | perceived_race, perceived_gender, perceived_age_band | labels from the subgrouping step, same level names as the fakes (`race`, `gender`, `age_band`) |
   | label_confidence | confidence of the perceived labels |
   | width, height, fps, duration_s | source format |
   | face_gate | 1 if the clip passes the real-set face gate |
   | primary | = face_gate (headline inclusion) |
   | identity_cluster | optional; when present, real CIs resample identities |
   | generator | `real` |

   Set `real_b1.data_root` in `eval_sets.yaml` and add `real_b1` to `active`.
2. **Preprocess** with the same commands as above (`BATCH=real_b1`). The same script applies the
   real rules from the view spec: the middle 5.0 s (clips shorter than 5.0 s are excluded), two
   renders per clip at 24 and 16 fps (`<clip_id>__fps24`, `__fps16`), never upscaled
   (`native` requires a 1280x704 source; CelebV-HQ at 512x512 is only valid in `face512`), and
   the same fixed median-face window for `face512`.
3. **Score** and **aggregate** as above. Once reals are scored, `aggregate` must fill section
   6.3 (calibrated threshold, AUC/AP/EER/TPR@5%FPR, real FPR by subgroup) and replace the
   provisional threshold; until that code lands, those rows stay `pending` in every snapshot.

## Add a detector

1. Create `eval/detectors/<name>/adapter.py` with a subclass of `eval.detectors.base.Detector`:
   `name`, `version` (bump whenever preprocessing changes), `checkpoint_sha256`,
   `preprocess_spec` (dict, the official recipe applied on top of the view),
   `default_threshold` + `threshold_source`, `report_note` (training-data caveat), and
   `load(device)`, `prepare(path) -> tensor` (CPU, runs in DataLoader workers),
   `score(batch) -> scores in [0, 1]` (higher = more likely generated).
2. Add one line to `REGISTRY` in `eval/detectors/registry.py`.
3. Record checkpoint source, license and SHA256 in `eval/LOG.md`, sanity-check against the
   authors' reported numbers (see `eval/sanity_aigvdb.py`), then score and aggregate:
   ```bash
   for v in native face512; do sbatch --export=ALL,DETECTOR=<name>,VIEW=$v,BATCH=fake_b1 eval/slurm/score.sbatch; done
   sbatch --export=ALL,DETECTOR=<name> eval/slurm/aggregate.sbatch
   python -m eval.compare
   ```
   Stubs with TODOs: `demamba`, `aigvdet`, `clip_probe`, `altfreezing`.

## Rules the code enforces

- A view spec whose content does not match its `view_hash`, or a different installed ffmpeg,
  is refused; changing a view means a new view name.
- `aggregate` refuses to mix scores with different `checkpoint_sha256`, `detector_version` or
  `view_hash` (`--allow-other-identities` ignores the old rows instead).
- Failed renders and failed scores are recorded with their error and retried on the next run.
