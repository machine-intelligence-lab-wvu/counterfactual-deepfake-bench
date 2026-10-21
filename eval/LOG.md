# Evaluation log

Every decision, version, checksum and view hash, newest section last.

## 2026-10-20: setup (Step 0-1)

**Plan.** `EVALUATION_PLAN.md` v2 committed on `eval-pipeline` (b197969). Updated in 47386b9 with
the DeCoF training-data wording and the fixed-window face512 rule below.

**Detector training data (DeCoF).** The released DeCoF checkpoint is most likely trained on
AIGVDBench's Open-Sora split (per the paper's default training set and the checkpoint name);
our generators are therefore likely unseen. Not confirmed by the authors. Our curated GenBuster
subset includes LTX-Video and HunyuanVideo, which are separate from DeCoF's training data but
not from AIGVDBench as a whole.
- Evidence: AIGVDBench (arXiv 2601.11035) Table 2 note, "Open-Sora is selected as the default
  training set"; the checkpoint's only top-level entry is `1_0.9994_val/` (epoch 1, val 0.9994),
  in line with in-domain Open-Sora (paper: 99.90 AUC on Open-Sora test).

**Environment.**
| Item | Value |
|---|---|
| Python / torch | NCSA module `python/miniforge3_pytorch/2.10.0`: Python 3.12.9, torch 2.10.0+cu129, torchvision 0.25.0 |
| Why 2.10.0 | 2.11/2.12 modules are CUDA 13 builds; they print "Requires NVIDIA driver 590+" on the login node (no driver there). Compute nodes run 595.71.05, so they would also work; 2.10.0 is pinned for reproducibility. |
| venv | `/projects/bjej/rahamed/fairdeep_eval/venv` (`--system-site-packages`), extras in `eval/requirements.txt`, binary wheels only (ARM; no dlib) |
| ffmpeg | conda-forge `ffmpeg 7.1.1 gpl_h0a60610_911`, `x264 1!164.3095 pl5321hac29afa_3`, prefix `/projects/bjej/rahamed/fairdeep_eval/ffmpeg`. `ffmpeg -version`: "ffmpeg version 7.1.1 Copyright (c) 2000-2025 the FFmpeg developers" |
| GPU | NVIDIA GH200 120GB, driver 595.71.05, partition `ghx4`, account `bjej-dtai-gh` |

**Weights and code (checksums).**
| Artifact | Source | SHA256 |
|---|---|---|
| `Weights/DeCoF.tar` (torch zip, 56.8 MB; keys `model`, `optimizer`, `epoch`) | `AIGVDBench/AIGVDBench` dataset @ `bf48acaa4920990af3dd2a511ea88e63354df305` | `4edb7b310cc729771e74b93f658c7fdc4f2e31fdfa617a88372a540d4f9e7b4a` (matches the hub's LFS hash) |
| CLIP ViT-L/14 `ViT-L-14.pt` | openaipublic.azureedge.net (URL used by the authors' `clip.py`) | `b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836` (matches the hash in the URL) |
| YuNet `face_detection_yunet_2023mar.onnx` | `opencv/face_detection_yunet` @ `3cc26e7f1014a5ee5d74a42acee58bafc9d0a310` | `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4` |
| DeCoF code | `github.com/LongMa-2025/DeCoF` @ `5f73e8dc4f8cd9faeed07d767c9517e3f2c66044` (pinned checkout in `$FAIRDEEP_EXT/src_DeCoF`, not copied into this repo: the repo has no license file) | - |

**Licenses.** AIGVDBench dataset (videos, splits, weights): CC-BY-4.0 (dataset card). DeCoF
GitHub repo: no license file. OpenAI CLIP weights: MIT (CLIP repo). YuNet: Apache-2.0 (OpenCV zoo).

**Where the inference code is.** `github.com/LongMa-2025/AIGVDBench` contains only README,
figures and split files (all 16 commits); there is no `test.py` there. The DeCoF code
(including `src/test.py`) is in the authors' DeCoF repo above.

**DeCoF video-level preprocessing (derived).** `test.py` is image-folder based (8 pre-extracted
JPGs per video). The video-level path combines:
- AIGVDBench section 7: "uniformly sampling 32 frames from its first 128 frames (or all
  available frames if the total is fewer than 128)", "center-cropped along the shorter side and
  resized to 256x256", PNG, and "only the first 8 of the 32 sampled frames are used";
- DeCoF `src/utils/data.py` test transform: `Resize((224,224))` -> `CenterCrop(224)` ->
  `ToTensor` -> `Normalize(ImageNet mean/std)` (not CLIP's mean/std);
- DeCoF `model.py`: frozen CLIP ViT-L/14 `encode_image` per frame -> (8, 768) -> `vit.ViT`
  (depth 2, 4 heads, mlp 768, mean pooling) -> 2 logits; `test.py` score = `softmax[:, 1]`.
Choices the sources leave open: sampling = `np.linspace(0, n-1, 32).astype(int)[:8]`
(n = 128 gives frames 0,4,...,28, the same frames as the DeCoF README rule "first 32 frames,
evenly select 8"); 256 resize = PIL bilinear; fp32 throughout with TF32 off (the authors' code
runs CLIP in fp32; bf16 is not used because it changes scores and compute is negligible).
For our 5.0 s views n = 120 (24 fps) or 80 (16 fps), so the 8 frames span 1.1 s / 1.1 s.
Adapter version `1+<hash of the spec dict>` (see `eval/detectors/decof/adapter.py`).

**Official threshold.** None stated in either paper. `test.py` takes `argmax` over the two
logits for accuracy, i.e. `softmax[:, 1] >= 0.5`. Provisional threshold = 0.5.

## 2026-10-20: views

| View | view_hash | Rule |
|---|---|---|
| native | `1e7dfa0b3c412dce` | first 5.0 s, native fps, 1280x704 passthrough (source must equal), x264 CRF 23 medium yuv420p, GOP 2 s, no scene-cut keys, threads 2, no audio, metadata stripped, bitexact |
| face512 | `330ecb1e37e36e82` | scale-to-cover (shorter side to 512, lanczos; 1280x704 -> 931x512), one fixed 512x512 window at the median YuNet face centre over all frames of the segment, shifted inward at frame edges (never padded); same rule for reals; same encode as native |

Decisions:
- face512 window is fixed per clip (user decision): a moving window would add a synthetic pan,
  which a frame-consistency detector can respond to. Subject = largest face per frame
  (`qc/faces.py` rule, score >= 0.6, >= 12 px). Clips with no face in any frame are `excluded`
  (logged with the frame count), not given a fallback window.
- Shift logging is per axis. A 1280x704 source scales to exactly 512 px tall, so the window
  always spans the short axis and is "shifted" on it by construction; `shifted_x` (long axis) is
  the informative count.
- x264 thread count is fixed (2) so the encode is reproducible; 36 parallel encodes per job.
- Outputs are verified with ffprobe (codec, pix_fmt, size, fps, exact frame count, single video
  stream, keyframes at 0/2/4 s). A failing output is deleted and the clip recorded `failed`.
- View videos: `$FAIRDEEP_VIEWS_ROOT/<view>/<view_hash>/<batch>/<clip_id>.mp4`.

## 2026-10-20: metrics

- Bootstrap: 1,000 resamples, seed 20261020, unit = counterfactual group. A group id names the
  same scene (setting, lighting, behavior, camera) in all three generators (checked on fake_b1:
  36 groups, one scene tuple each; only the duration rounding differs by fps), so one resample of
  group ids is shared across generators and breakdowns.
- CF spread uses the population std (ddof = 0) across a group's clips; groups with < 2 included
  clips are dropped.
- Factor attribution: OLS type-II ANOVA with every factor fixed (partial eta^2 and SS share),
  lighting x race added as an interaction in a second OLS, and a REML mixed model with a random
  intercept per counterfactual group for the variance components. Scene factors are constant
  within a group, so their effects come from between-group differences only.
- `duration_nominal` = requested length (5 or 6 s). Both views trim to 5.0 s, so it describes
  the generation request, not the scored segment length.
- Palette: generators take reference categorical slots 1-3 (blue `#2a78d6`, orange `#eb6834`,
  aqua `#1baf7a`) in fixed order; magnitude uses one sequential blue ramp. The palette
  validator needs node, which is not installed here; the three slots are the reference
  instance's pre-validated first three.

## 2026-10-20: Step 3 sanity check

**AIGVDBench test videos through our DeCoF adapter** (job 3423673, GH200, 32.6 s for 100 videos).
20 test-split `Video_id`s (seed 20261020), the same ids from each of Real, Open-Sora, LTX,
HunyuanVideo, Wan2.1 (T2V), read straight out of the release zips at `bf48acaa`; scored as
released (all already H.264), no view applied. AUC = each generator's 20 vs the 20 reals;
interval = 2,000 bootstrap resamples of reals and fakes.

| Source | Mean score | Acc @ 0.5 | AUC (ours) | 95% interval | AUC (paper, Table 3) |
|---|---|---|---|---|---|
| Real | 0.063 | 1.00 | - | - | - |
| Open-Sora | 0.984 | 1.00 | 100.00 | [100.0, 100.0] | 99.90 |
| LTX | 0.333 | 0.30 | 78.75 | [64.0, 91.8] | 87.74 |
| HunyuanVideo | 0.191 | 0.15 | 65.25 | [46.0, 81.8] | 79.82 |
| Wan2.1 | 0.089 | 0.05 | 56.75 | [38.7, 73.8] | 72.90 |

Every reported AUC lies inside our interval, and the ordering matches (Open-Sora > LTX >
HunyuanVideo > Wan2.1). Our point estimates for the three non-training generators are 9-16
points lower; with 20 vs 20 the intervals are 28-35 points wide, so this sample cannot tell a
small protocol difference from noise. Open-Sora at 100 AUC with every clip >= 0.5 is in line
with an Open-Sora-trained checkpoint. Paper values were mapped to generators by column order
from the arXiv HTML (garbled headers); check against the PDF before quoting them.

**20 of our clips end to end** (7 LTX, 7 Wan, 6 Hunyuan, all primary; ids in
`eval/tests/ids20_e2e.txt`): 20/20 rendered and verified in both views, 0 excluded, 0 long-axis
window shifts; 20/20 scored. face512 scores are higher than native for all 20 clips (Pearson r
= 0.913 between views). Re-rendering 2 clips into a separate tree gave byte-identical files.

Timing (1 GH200, 72 CPUs): native render ~10 s per clip per worker, face512 ~28 s (YuNet on
every frame); scoring 3.5 (native) / 6.4 (face512) clips/s with 16 workers and batch 20,
including decode; aggregate ~40-50 s per view (1,000 bootstrap resamples).

## 2026-10-20: Step 4, full run on fake_b1

**Jobs.** Render: native array 3423870 (4 shards, 4-22 min each), face512 shards 0-1 in array
3423871 (17 min each). The never-started remainder (3423871_2-3, 3423872-4; Slurm estimated a
start of 2026-10-21 16:45) was replaced by single-wait chained jobs sized from the measured runs:
3424790/3424791 (render + score face512 shards 2/3; 72 CPUs, 24 GB, 35 min limit; ran 21/19 min)
and score + aggregate 3424789, which was OOM-killed after 45 s (DataLoader prefetch 4 x 30
workers x batch 32 exceeded 40 GB; the 7 GB measured on the 20-clip run never filled the queue).
Fixed with prefetch 2 (`--prefetch`) and resubmitted as 3425083 (32 CPUs, 40 GB, 25 min limit;
ran 5 min, peak 41.3 GB, so the next scoring job should ask for 48 GB). The chained jobs started
47-57 min after submission. Scoring ran at ~28 clips/s on one GH200 after the decode change in
fd666a3 (stop at the last sampled frame; identical input tensors).

**Coverage.** native: 4,536/4,536 rendered and scored. face512: 4,532 rendered and scored, 4 LTX
clips excluded (no face found by YuNet in any frame), 4 windows shifted on the long axis (max
142 px). 0 render failures, 0 scoring failures. primary: 3,936 (native) / 3,932 (face512).

**Aggregation.** The first snapshots (20261020-2307/-2308) showed zero-width intervals for
levels present in a single counterfactual group (HunyuanVideo has 9 groups, so many scene
levels); resampling whole groups cannot express uncertainty there. Those levels now have no
interval (hollow marker). Reports also state that a max-min gap is non-negative by construction,
that OLS p values ignore clustering, and that the mixed model's group variance is 0 (scene fixed
effects absorb between-group variation). The superseded snapshots were deleted before commit.

**Headline (primary clips; DeCoF; provisional threshold 0.5):**

| | native mean [95% CI] | native det. rate | face512 mean [95% CI] | face512 det. rate |
|---|---|---|---|---|
| LTX 2.3 | 0.375 [0.306, 0.450] | 34.6% | 0.544 [0.474, 0.617] | 55.7% |
| Wan 2.2 | 0.063 [0.042, 0.087] | 3.1% | 0.159 [0.122, 0.198] | 11.2% |
| HunyuanVideo 1.5 | 0.149 [0.096, 0.208] | 11.6% | 0.348 [0.269, 0.430] | 32.3% |

## 2026-10-21: WVU lab server environment; DeMamba adapter

**Lab server (x86_64, RTX PRO 5000 Blackwell).** `eval_env/env_lab.sh` mirrors `eval/env.sh`: torch
2.10.0 + torchvision 0.25.0 (cu128 wheels; cu129 on DeltaAI), conda-forge ffmpeg 7.1.1 build 911
with x264 1!164.3095 (x86 builds of the pinned packages; `ffmpeg -version` matches, so both view
specs pass `--check`), the same Python pins, plus `setuptools<81` (DeCoF's vendored CLIP imports
`pkg_resources`). DeCoF.tar, ViT-L-14.pt and YuNet match their pinned SHA256.

**Cross-platform check (14 LTX/Wan clips of `ids20_e2e.txt`).** native renders are identical to
DeltaAI's render records; face512 windows move by at most 1 px (YuNet floats, x86 vs ARM). DeCoF
scores still differ: native max |d| 0.104 (mean 0.035), face512 max |d| 0.161 (mean 0.051), with 2/14
face512 decisions flipped at 0.5. Inputs are identical for native, so the difference is the
platform (CPU decode/resize, GPU, CUDA build), not the view. **Scores from the two platforms must
not be mixed** - `aggregate` checks checkpoint and view hashes, not platform. All of fake_b1 is
therefore re-scored on the lab server, so that real_b1 (scored here) is compared against fakes
scored on the same machine.

**DeMamba adapter** (`eval/detectors/demamba/`). Weights are ours:
`Ahsanz/DeMamba-GenVideo100K@27468b8` `best_acc.pth` (SHA256 f89897c7...56ce17, epoch 15), trained
on GenVideo-100K with a single-GPU adaptation of github.com/chenhaoxing/DeMamba. The authors have
not released weights (their issue #16). Model code is our standalone evaluator's inference copy of
DeMamba.py / mamba_base.py / pscan.py; the checkpoint loads strictly (transformers 5.20.2).
Preprocessing matches the authors' val pipeline: 2 fps for clips >= 4 s (every round(fps/2)-th
frame), centre 8-frame window (authors: random), 10% centre trim of the long side, cv2 INTER_LINEAR
to 224x224, ImageNet mean/std. Open points settled:
- channel order RGB: our training dataloader applies `cv2.cvtColor(BGR2RGB)` (confirmed by the
  person who trained it; the checkpoint README's "BGR" line refers to OpenCV's decode);
- fp32, TF32 off (training used bf16 autocast; bf16 moves scores by <= 0.04 on 120 clips);
- frames are sampled from the decoded view, not extracted to JPEG first as the authors do.
`prepare()` gives tensors identical to the standalone evaluator on 53 view clips. Not yet
sanity-checked against GenVideo validation numbers (accuracy 88.74%, AUC 96.67%): no copy of
GenVideo-Val on this server.

## 2026-10-21: real_all (unfiltered CelebV-HQ) in four views

**Batch.** `real_all` = all 2,221 fetched CelebV-HQ segments, no filtering (`filter_accepted` /
`filter_reason` kept per clip; 1,785 accepted). FairFace labels for 2,084 (436 rejected clips
labelled from the raw segment, `real/label_raw.py` on real-half). `real_b1` is inactive.

**Views.** New `native_up` / `native_up_2s` (mode `cover_window`): scale up or down to cover
1280x704 at the median face centre (frame centre if no face); fakes pass through. Real renders
ok / total: native_up_2s 4432/4442, native_up 1855/1892, face512_2s 4412/4442 (30 excluded: no
face), face512 1847/1892. Failures are `verify: frames N-1 != N` on 16 fps renders (open).

**AUC, all generators, all reals / filter-accepted reals** (`results/compare/real_all/`):

| view | DeCoF | DeMamba |
|---|---|---|
| native_up_2s | 0.565 / 0.550 | 0.930 / 0.926 |
| native_up | 0.585 / 0.571 | 0.938 / 0.935 |
| face512_2s | 0.679 / 0.664 | 0.937 / 0.931 |
| face512 | 0.699 / 0.684 | 0.936 / 0.931 |

Filtering moves no generator's AUC by more than 0.022. DeCoF on Wan 2.2 is below chance in
full frame (0.37-0.39) and at chance on face crops (0.51-0.53).
