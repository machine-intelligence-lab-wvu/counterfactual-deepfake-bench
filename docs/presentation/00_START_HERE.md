# Counterfactual DeepFake Bench — evaluation results pack

Upload this file first. It says what every other file in this folder is, and carries the headline
numbers so the rest can be read selectively rather than all at once.

**Updated 2026-10-22.** Four detectors are now wired, all four against the unfiltered real set, and
each one checked against its own published benchmark first. That last step changed the story — see
"The headline" below. All intervals are 95%, from 1,000 bootstrap resamples of whole
**counterfactual groups** (not clips).

---

## What the benchmark is, in four lines

Synthetic text-to-video clips of people, generated so that **demographic presentation is the only
deliberately varied factor**. 56 intersectional cells (7 race × 2 gender × 4 age). A
*counterfactual group* fixes one content recipe (scene, lighting, behaviour, camera, attire,
duration) and one seed, then renders it across all 56 cells — so balance is structural. Detectors
score this against a real half drawn from CelebV-HQ.

## Corpus as scored

| arm | clips | note |
|---|---|---|
| LTX 2.3 | 2,016 | 36 groups, 20 steps cfg 3.0, bf16 |
| Wan 2.2 | 2,016 | 36 groups, **4-step distill LoRA, cfg 1.0** |
| HunyuanVideo 1.5 | 1,008 | 18 groups, 20 steps cfg 6.0 |
| **real (CelebV-HQ)** | **2,221** | `real_all`: every fetched segment, unfiltered |
| LTX 2.5 | 1,233 / 2,016 | generation in progress, **not yet scored** |

**Detectors** — four, all run on the same views, same bootstrap, same thresholds:

| detector | mechanism | weights |
|---|---|---|
| **DeMamba** | spatiotemporal Mamba | trained in-house on GenVideo-100K (authors released none) |
| **DeCoF** | CLIP ViT-L/14 frame features + temporal ViT | authors' AIGVDBench checkpoint |
| **V-PVP** | frozen VideoMAE-B/16 + velocity-gated readout | authors' AIGVDBench-trained head |
| **D3** | X-CLIP-B/16, std of 2nd-order feature — **training-free** | none needed |

**Views** (preprocessing is a first-class variable): `native_up` / `native_up_2s` (full frame
scaled to cover 1280×704, fixed window at median face centre — **excludes nothing**) and
`face512` / `face512_2s` (fixed 512² face crop — drops many reals).

---

## The headline: three of four detectors collapse to chance, and it is not an implementation bug

Each detector was first reproduced on **its own published benchmark**, then run on Counterfactual DeepFake Bench:

| detector | its own benchmark | our AUC | paper / card | **Counterfactual DeepFake Bench AUC** |
|---|---|---|---|---|
| **DeMamba** | GenVideo-Val | 96.94 | 96.67 | **0.930 – 0.938** |
| **D3** | GenVideo-Val | **98.60** | 97.72 | **0.467 – 0.497** |
| **V-PVP** | AIGVDBench-150 | **97.70** | 95.28 | **0.440 – 0.519** |
| **DeCoF** | AIGVDBench-150 | 79.28 | 92.20 | **0.565 – 0.699** |

D3 and V-PVP **match or beat their published numbers** on the benchmarks they were built for, then
land at chance on ours. The adapters are correct; the generalization is not there. Only DeMamba
transfers, and it is the one detector trained on the broadest generator set.

### Per generator (`native_up_2s`, all 2,221 reals)

| detector | LTX 2.3 | Wan 2.2 | HunyuanVideo 1.5 | pooled |
|---|---|---|---|---|
| DeMamba | 0.897 | 0.952 | 0.960 | **0.930** |
| DeCoF | 0.738 | **0.372** | 0.536 | 0.565 |
| V-PVP | 0.503 | 0.656 | **0.303** | 0.512 |
| D3 | **0.396** | 0.516 | 0.523 | 0.467 |

Three detectors are **below chance on at least one generator** — their fakes score as *more real*
than real video. And no two detectors agree on which generator is hardest: DeCoF says Wan, D3 says
LTX 2.3, V-PVP says Hunyuan.

### Preprocessing moves DeCoF, not the others
DeCoF pooled AUC: 0.565 (`native_up_2s`) → 0.699 (`face512`), a 13-point swing from the crop rule
alone. DeMamba is flat across all four views (0.930–0.938), D3 (0.467–0.497) and V-PVP
(0.440–0.519) likewise. A face-crop view helps DeCoF specifically — and drops most real clips.

---

## Subgroup results — read these only for DeMamba

A subgroup AUC gap is only meaningful where the detector works at all; for a detector at chance,
subgroup differences are noise around 0.5. **DeMamba is the only arm where subgroup gaps are
interpretable.** `native_up_2s`, pooled:

| axis | worst | best | gap [95% CI] |
|---|---|---|---|
| race | East Asian 0.916 | MENA 0.973 | 0.057 [0.036, 0.097] |
| age | **18-29 0.889** | **60+ 0.955** | 0.067 [0.044, 0.093] |
| gender | female 0.908 | male 0.939 | 0.030 [0.011, 0.051] |
| race × gender | East Asian female 0.893 | MENA female 0.978 | 0.085 [0.061, 0.157] |

All intervals exclude zero, so the gaps are real but modest. For contrast, DeCoF's gaps are far
larger (race 0.148, age 0.148, South Asian male 0.452 vs White female 0.694) — but DeCoF is at
0.565 overall, so those gaps are partly variation in *how* it fails.

**The age effect reverses between detectors:** DeCoF is worst on 60+, DeMamba is *best* on 60+.
Direction is a property of the detector, not the data.

## Two further results

**Generator identity dominates variance, but age beats every scene factor.** DeCoF `native_up_2s`
type-II ANOVA share of sum-of-squares: generator 27.1%, age_band 5.5%, setting 3.9%, behaviour
3.4%, race 2.7%, lighting 1.5%, gender 0.5%, residual 51.9%.

**The prompt is not the label.** FairFace verification of what the generators actually rendered:

| match rate | LTX 2.3 | Wan 2.2 | Hunyuan 1.5 | all |
|---|---|---|---|---|
| gender | 0.946 | 0.956 | 0.987 | 0.959 |
| age band | 0.770 | 0.628 | 0.789 | 0.724 |
| race | 0.654 | 0.490 | 0.625 | 0.589 |
| **full cell** | 0.463 | 0.284 | 0.480 | **0.403** |

Race fidelity is bimodal — Black 0.967, White 0.927, but MENA 0.314, Latino 0.349, South Asian
0.384 (Wan's South Asian: 0.087). Requested South Asian reads as Hispanic 27.8% of the time;
requested MENA reads as White 33.0%. Only 42.9% of 30-44 requests land in that band.

**Filtering the reals changes nothing.** AUC on all 2,221 reals vs the 1,785 that pass the
real-half filter: no generator moves by more than 0.022, on any view or detector.

---

## Caveats to state on any slide

- **Threshold 0.5 is provisional** for detection-rate tables; real-FPR tables use a threshold
  calibrated to 5% FPR over all reals.
- **DeMamba's weights are ours, not the authors'** — it reproduces the model card (AUC 96.94 vs
  96.67, accuracy 88.32% vs 88.74%), but published DeMamba numbers are not directly comparable.
- **DeCoF under-reproduces its reference** (79.28 vs 92.20 on AIGVDBench-150), so its Counterfactual DeepFake Bench
  number may be pessimistic; D3 and V-PVP over-reproduce theirs, so theirs is not.
- **The real half is skewed.** 51 of 56 cells; White 1,418 vs South Asian 56; male 1,512 vs female
  690. Subgroups under 30 real renders are reported "not estimable".
- **Real labels are FairFace-inferred, synthetic labels prompted-then-verified** — different kinds
  of evidence, and FairFace is weaker on darker skin and older faces.
- **The arms are not sampling-matched.** Wan ran a 4-step distill LoRA at cfg 1.0 with an inert
  negative prompt; LTX and Hunyuan ran reference sampling.
- **Scores are platform-dependent** — ARM vs x86 differ by up to 0.104 on identical inputs.
  Everything was re-scored on one machine.
- Mixed-model group variance is 0 (scene fixed effects absorb it); OLS p-values ignore clustering;
  a max−min gap is non-negative by construction.

---

## Files in this folder

### Upload these first (the core eight)

| file | what it gives you |
|---|---|
| `00_START_HERE.md` | this file |
| `tables/17_sanity_reference_benchmarks.csv` | **the generalization-collapse table** — each detector on its own benchmark vs ours |
| `tables/01_realfake_auc_by_generator.csv` | AUC / AP / EER per detector × view × generator |
| `tables/02_worstgroup_auc_gaps.csv` | worst vs best subgroup AUC with CIs |
| `tables/10_fairface_fidelity.csv` | prompt-vs-perceived match rates |
| `figures/01_detection_rate_by_detector_view.png` | all four detectors at a glance |
| `figures/03_subgroup_auc_demamba.png` | the subgroup AUC chart for the one detector that works |
| `GENERATION_OVERVIEW.md` | how the corpus was built |

### Add as the discussion needs them

**Tables** — all detector tables carry `detector` and `view` columns over 4 detectors × up to 4 views
- `00_cross_detector_headline.csv` — mean score, detection rate, demographic gaps, all 20 snapshots
- `03_subgroup_auc_full.csv` — every subgroup AUC incl. "not estimable" notes
- `04_real_fpr_by_subgroup.csv`, `05_real_fpr_gaps.csv` — false positives on reals
- `06_detection_rate_by_subgroup.csv` / `06b_…_scene_factors.csv` / `06c_…_56cells.csv`
- `07_factor_attribution_anova.csv` — variance decomposition
- `08_counterfactual_spread.csv` — within-group spread across the 56 cells
- `09_inclusion_coverage.csv` — clips surviving each stage, per batch and view
- `16_sensitivity_inclusion_set.csv` — how results move with the inclusion rule
- `18_sanity_per_source.csv` — per-generator reference-benchmark numbers vs the papers
- `11_confusion_race.csv`, `12_confusion_age_band.csv` — requested vs perceived
  *(the age confusion drops FairFace's ambiguous 40-49 bin, so its diagonal reads higher than the
  fidelity table; quote `10_fairface_fidelity.csv` for match rates)*
- `13_fidelity_by_56cells.csv`, `14_qc_acceptance.csv`, `15_quality_proxies.csv`

**Figures** — `02_mean_score_by_detector_view.png`, `04`/`06` ROC curves,
`05_subgroup_auc_decof.png`, `07_factor_attribution_decof.png`,
`08_real_fpr_by_subgroup_demamba.png`, `09_heatmap_56cells_demamba.png`,
`10_score_distribution_demamba.png`, `11`–`13` FairFace fidelity figures

**Narrative** — `CROSS_DETECTOR_SUMMARY.md` (generated comparison over all 20 snapshots),
`REAL_ALL_FILTERED_VS_UNFILTERED.md` (all four views), `METHODS_LOG.md` (checkpoints, SHA256s,
view hashes, protocol derivations, every reproduction check and decision)

**`build_pack.py`** regenerates this folder from the newest snapshots — it follows the `latest`
symlinks, so re-run it after new scoring and only this file and `GENERATION_OVERVIEW.md` need
hand-editing.

### Deliberately left out
The full `REPORT.md` files (50–80 KB each, mostly 56-cell tables) and all PDF duplicates of the
figures. They are in `results/` in the repo.
