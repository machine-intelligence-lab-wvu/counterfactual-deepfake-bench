# DeepFake Bench: Evaluation Plan (v2, incremental)

CITeR project 25F-01W · Curating and Evaluating AI-Generated Video Content

## 0. Framing

This is a **dataset and benchmark**, not a bias study. Results are breakdowns by subgroup,
generator, and scene factor. Use "per-subgroup", "worst-subgroup", "subgroup gap",
"counterfactual consistency". Never use the two excluded words (listed in `eval/tests/test_pipeline.py::test_metric_words`) in code, file names, tables, or text.

## 1. Design principle: score once, aggregate any time

Data arrives in batches (fakes now, more fakes later, reals later). The pipeline must give a
usable result as soon as any batch is scored, and fold in later batches without re-running
earlier ones.

- **Scoring is per clip and append-only.** A clip is scored once per
  (detector, checkpoint, preprocessing view). Scores are never overwritten.
- **Metrics are recomputed from all scores available** each time `aggregate` runs.
  Aggregation is cheap (CPU, minutes) and fully reproducible.
- **Every result snapshot records exactly which clips it used**, so numbers in slides can be
  traced to a snapshot.
- **Metrics that need missing data are marked `pending`**, never silently skipped or filled.

## 2. Data

| Batch | Content | Status | Location |
|---|---|---|---|
| `fake_b1` | 4,536 generated clips: LTX 2.3 (2,016), Wan 2.2 (2,016), HunyuanVideo 1.5 (504) | on DeltaAI | `/work/nvme/bjej/rahamed/fairdeep/eval/fairdeep-bench/` |
| `fake_b2` | ~500 more generated clips | pending | TBD |
| `real_b1` | ~3,000 CelebV-HQ real clips with perceived subgroup labels | pending (subgrouping in progress) | TBD |

Sources: generated clips from `Ahsanz/fairdeep-bench` (LTX, Wan) and
`robinrizwan/fairdeep-bench` (Hunyuan).

Generated metadata per clip: generator, cell (race × gender × age band; 56 cells),
counterfactual group, setting, lighting, behavior, camera, duration, seed, prompt,
technical QC, face QC.

Real metadata per clip (from the subgrouping step): source id, perceived race, gender, age band,
label confidence, resolution, fps, duration.

### Clip inclusion

Score **every** clip in a batch. Inclusion is decided at aggregation time by flags:

- `primary`: technical QC pass AND face QC pass (fakes); passes the real-set face gate (reals).
- `all`: everything scored (sensitivity analysis only).

All headline numbers use `primary`.

## 3. Preprocessing views

A **view** is a frozen preprocessing recipe applied identically to reals and fakes. Each view has
a spec file and a hash; scores are keyed by view hash. If a spec changes, it is a new view.

| View | Purpose | Spec |
|---|---|---|
| `native` | Full frame, as generated | 1280×704; native fps (LTX/Hunyuan 24, Wan 16; never resample fakes); first 5.0 s; H.264 CRF 23, preset medium, yuv420p, keyframe every 2 s; no audio; metadata stripped |
| `face512` | Face-centred square, matches face-cropped real datasets | Scale-to-cover (shorter side to 512, downscale only), then one fixed 512×512 window per clip centred on the median YuNet face centre over the clip, shifted inward at frame edges (never padded); same rule for reals; same fps, duration, and encoding rules as `native` |

Rules:

- Reals are produced at **both 24 and 16 fps**. Per-generator metrics use fps-matched reals.
- Reals shorter than 5.0 s are excluded. Reals are trimmed from the middle segment.
- If a source is smaller than the view's resolution, that clip is excluded from that view
  (never upscale).
- One script, one pinned ffmpeg version for every clip. Record `ffmpeg -version` in the view spec.

**Why two views:** CelebV-HQ clips are face-cropped. If the reals are 512×512, only `face512` is
a like-for-like comparison. `native` remains useful for fake-only analyses. Scoring fakes in both views
now means no rescoring later.

## 4. Detectors

| Detector | Family | Status |
|---|---|---|
| DeCoF | Frame consistency (CLIP features + temporal module) | **first** |
| DeMamba | Video-level spatiotemporal | next |
| AIGVDet | RGB + optical flow | planned |
| CLIP probe (UnivFD-style) | Frozen foundation features | planned |
| AltFreezing | Face-forgery specialist | planned |

DeCoF checkpoint: official AIGVDBench release (`AIGVDBench/AIGVDBench`, `Weights/DeCoF.tar`).
The released DeCoF checkpoint is most likely trained on AIGVDBench's Open-Sora split (per the
paper's default training set and the checkpoint name); our generators are therefore likely
unseen. Not confirmed by the authors. Our curated GenBuster subset includes LTX-Video and
HunyuanVideo, which are separate from DeCoF's training data but not from AIGVDBench as a whole.
State this wherever DeCoF results appear.

All detectors: official checkpoint, zero-shot, official preprocessing applied on top of the view,
one video-level score in [0, 1] (higher = more likely fake).

## 5. Storage layout

```
eval/
  manifests/
    fake_b1.csv  fake_b2.csv  real_b1.csv     one row per clip + all metadata + flags
    eval_sets.yaml                            which batches make up the current eval set
  views/
    native.yaml  face512.yaml                 frozen specs + hash
results/
  scores/<detector>/<view>/<batch>/part-*.parquet
      columns: clip_id, batch, score, status, error, detector, detector_version,
               checkpoint_sha256, view, view_hash, git_commit, gpu, timestamp
  snapshots/<detector>/<view>/<YYYYMMDD-HHMM>/
      manifest_used.csv  tables/*.csv  figures/*.png|pdf  REPORT.md  snapshot_meta.json
  snapshots/<detector>/<view>/latest -> <newest snapshot>
  compare/<YYYYMMDD-HHMM>/                  cross-detector tables and figures
  coverage.md                               scored / pending / failed per batch × detector × view
```

Rules:

- Scores are append-only. Rerunning a batch skips clips already scored with the same
  (detector, checkpoint_sha256, view_hash).
- Failed clips get `status = failed` and an `error`; they are retried on the next run and reported.
- `aggregate` refuses to mix scores with different `checkpoint_sha256` or `view_hash` for the same
  detector and view.

## 6. Metrics

### 6.1 Available now (fakes only, no threshold)

| Metric | Definition |
|---|---|
| Score distribution | Per generator, subgroup (race, gender, age band, 56 cells), and scene factor |
| Mean score + 95% CI | Same breakdowns; bootstrap resampling whole counterfactual groups |
| Subgroup gap (score) | max − min of mean score across levels of each attribute |
| CF spread | Mean over groups of the std of score across the group's cells |
| Factor attribution | Mixed model `score ~ race + gender + age_band + setting + lighting + behavior + camera + duration + generator + (1 \| group)`; variance components, ANOVA partial η², and `lighting × race` |

### 6.2 Provisional (fakes only, provisional threshold)

Threshold = the detector's official default (or 0.5 if none). Marked **provisional** in every
table and figure, and replaced automatically once reals exist.

| Metric | Definition |
|---|---|
| Detection rate | Share of fakes with score ≥ threshold, by every breakdown |
| Flip rate | Share of counterfactual groups whose clips get different decisions |

### 6.3 When reals arrive

Threshold = score at which 5% of fps-matched reals are flagged fake (one global threshold per
detector and view; never per subgroup).

| Metric | Definition |
|---|---|
| AUC, AP, EER, TPR@5%FPR | Overall and per generator (each generator's fakes vs fps-matched reals) |
| Real FPR | By perceived race, gender, age band, race × gender |
| Detection rate, flip rate | Recomputed at the calibrated threshold |
| Worst-subgroup AUC, subgroup gap | Per attribute |

All CIs: 95%, 1,000 bootstrap resamples, fixed seed. Fakes resample by counterfactual group;
reals resample by clip (or by identity if identity clusters are available).

### 6.4 Generator benchmark (Track A, detector-independent)

QC acceptance per cell, demographic fidelity (perceived vs requested cell, FairFace/MiVOLO),
motion, visual quality. Runs separately; same aggregation rules.

## 7. Figures (per snapshot)

PNG 300 dpi + PDF, consistent style, colorblind-safe, readable on a 4:3 slide. Provisional
figures carry a "provisional threshold" label.

- Score distributions by generator (and real vs fake once reals exist)
- Mean score / detection-rate heatmap: 56 cells × generator
- Per-subgroup bars with CIs (race, gender, age band)
- Scene-factor bars with CIs
- CF spread distribution; flip rate by generator
- Factor attribution: variance share by factor
- ROC curves per generator (reals only)
- Real FPR by subgroup (reals only)
- Example strip: highest- and lowest-scoring clips with metadata

## 8. Workflow

```
1. build manifest for a new batch      eval/manifests/<batch>.csv
2. preprocess batch for each view      Slurm array, CPU-heavy, GPU node
3. score batch                         python -m eval.run --detector D --view V --batch B
4. aggregate                           python -m eval.aggregate --detector D --view V
5. compare (optional)                  python -m eval.compare
```

Steps 2–3 run per batch, independently. Step 4 can run at any time and always uses everything
scored so far. Adding `fake_b2` or `real_b1` = steps 1–4 for that batch only.

## 9. Compute (DeltaAI)

- Partition `ghx4`, account `bjej-dtai-gh`. Do not use `ghx4-interactive` (2× charge).
- ARM (aarch64): use NCSA's PyTorch module or conda-forge builds; avoid dlib.
- 1 GPU per job with many CPUs (decoding is the bottleneck). Large batches, many DataLoader
  workers, bf16 where the official model allows it.
- Shard large jobs as Slurm arrays; every job resumable.

## 10. Open items

- [ ] CelebV-HQ real clip format (resolution, fps, duration) → decides whether `native` applies to reals
- [ ] Location and manifest of `fake_b2`
- [ ] DeCoF official default threshold
- [ ] Remaining detectors' checkpoint availability
