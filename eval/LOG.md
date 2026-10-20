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
