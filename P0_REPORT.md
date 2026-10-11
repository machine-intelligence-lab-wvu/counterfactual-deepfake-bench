# P0 — Environment Recon & Feasibility Report

**FairDeep-Fake Bench / controlled synthetic video generation**
Date: 2026-08-06 · Host: 4× RTX PRO 5000 Blackwell · ComfyUI v0.30.0 (`7972b5ba`)

---

## 1. Headline

**Wan 2.2 T2V-A14B works end-to-end today and the full 5,750-clip run is feasible inside the runway** — but only if clip duration is skewed short, and only if the GPU-sharing question below is resolved. Verified: 6 real 720p clips generated, correct demographic compliance on the pilot cell, distinct identities across seeds.

Two plan assumptions need correcting before P1 (§5), and one ethics landmine was found in the LTX ecosystem (§6).

---

## 2. Hardware & contention — needs your decision

| GPU | Total | Used by other job | Free |
|---|---|---|---|
| 0–3 | 48.9 GiB each | 28–46 GiB (oscillating) | 2–20 GiB (oscillating) |

All four GPUs are running **your own** verl RL job (`ray::WorkerDict.actor_rollout_ref_update_actor`, uptime 1d08h at time of recon). Host RAM is also committed: 48 GiB free of 270 GiB, which limits CPU-offload headroom.

**Good news:** I benchmarked successfully anyway. Wan 2.2 fp8 ran with as little as ~6 GiB free VRAM — ComfyUI's offloading absorbed the pressure, and there were **zero OOMs across 6 generations**. So the RL job is not a hard blocker.

**But:** the measured numbers below are *contended* numbers, and there is real OOM risk at RL memory peaks during an unattended 24/7 run. **Decision needed:** do we (a) share as-is and accept occasional OOM + retry, (b) get 1–2 GPUs dedicated, or (c) wait for the RL job to finish? Recommendation: **(b)** — reserve 2 GPUs for generation, leave 2 for RL. That fits the runway with margin and makes the batch driver's life much easier. I have not touched your job.

---

## 3. Measured throughput (Wan 2.2 T2V-A14B, fp8 + 4-step LoRA)

Config: MoE two-expert sampling, 4 total steps split 2+2, cfg 1.0, shift 5.0, euler/simple, `wan_2.1_vae`, 16 fps, contended GPU.

| Resolution | Frames | Clip length | Time/clip | Compute per s of video |
|---|---|---|---|---|
| 640×640 | 81 | 5.06 s | 82.4 s cold / **44.1 s** warm | 8.7 s |
| 1280×720 | 81 | 5.06 s | **142.2 s** (×2 runs, identical) | 28.1 s |
| 1280×720 | 121 | 7.56 s | **278.7 s** | 36.9 s |
| 1280×720 | 161 | 10.06 s | **458.7 s** | 45.6 s |

**Calibration:** the template's reference 4090D does 640² in 71 s warm; we do 44.1 s. This box is ~1.6× faster *even while contended*.

### Cost scales ~frames^1.7, not linearly

This is the single most budget-relevant finding. A 10 s clip costs **3.2×** a 5 s clip, not 2×. Duration policy dominates the schedule:

| Duration policy | Avg s/clip | 5,750 clips | On 4 GPUs | On 2 GPUs |
|---|---|---|---|---|
| All 5 s | 142 s | 227 GPU-h | 2.4 d | 4.7 d |
| **70/20/10 skew (5/7.5/10 s)** | **201 s** | **321 GPU-h** | **3.3 d** | **6.7 d** |
| Uniform 5/7.5/10 s | 293 s | 468 GPU-h | 4.9 d | 9.8 d |
| All 10 s | 459 s | 733 GPU-h | 7.6 d | 15.3 d |

Runway to the P4 freeze (Aug 14) is **8 days**. **Recommendation: the 70/20/10 skew.** It keeps the plan's 5–10 s spec and its within-cell duration variation, fits 2 dedicated GPUs with regeneration headroom, and costs 31% less than uniform sampling. Uniform-on-2-GPUs (9.8 d) misses the freeze.

---

## 4. Software state

| Component | Status |
|---|---|
| ComfyUI v0.30.0, 825 node classes | ✅ boots, HTTP API verified |
| Python env | ✅ `/.venv` via `uv` (system `python3` has no pip/ensurepip — needs root, avoided) |
| torch 2.11.0+cu128 | ✅ `sm_120` kernels present, bf16 verified on all 4 devices |
| Wan 2.2 T2V fp8 weights | ✅ ~36 GiB downloaded & placed |
| VideoHelperSuite | ✅ installed (needed `opencv-python-headless`, `imageio-ffmpeg`) |
| HunyuanVideo 1.5 / LTX 2.3 | ⬜ not downloaded — pending model-set decision (§6) |
| QC models (FairFace, MiVOLO, ArcFace, RetinaFace) | ⬜ not installed — P1 dependency |

Disk: **2.9 TB free.** Not a constraint.

ComfyUI core is unmodified; a server is currently running on GPU 2, port 8188.

### Files delivered
- `fairdeep-datagen/` scaffold (`specs/ renderers/ driver/ qc/ workflows/ manifests/`)
- Working API-format Wan 2.2 T2V workflow builder + timing harness (in session scratchpad, to be promoted into `driver/` at P1)

---

## 5. Two plan corrections needed before P1

**5.1 — fps is 16, not 24.** Wan 2.2 T2V-**A14B** is trained at **16 fps** (the bundled template hardcodes 16; 24 fps belongs to the Wan 2.2 5B TI2V model). Generating at 24 fps is off-distribution and would inject a generator artifact that correlates with nothing we control — bad for a bias benchmark. Also, frame count must satisfy **4k+1** (VAE temporal compression of 4): 81 / 121 / 161 frames = 5.06 / 7.56 / 10.06 s. Plan §6.3's "121–241 frames @ 24 fps" should become "81–161 frames @ 16 fps."

Note this makes **fps a cross-generator confound**: Hunyuan 1.5 and LTX 2.3 have their own native rates. Either normalize all clips to a common fps in post, or treat fps as a declared per-generator property. Recommend the latter plus reporting it — resampling introduces its own detectable artifacts.

**5.2 — background people threaten the single-face QC gate.** Both 720p office samples rendered faint background figures at desks. Plan §7.1 rejects any clip without *exactly one* face, so this could cause large, **scene-correlated** rejection rates — which is exactly the kind of confound §5.3 is meant to prevent. Fixes: add crowd terms to the negative prompt, prefer tighter framing, and add "empty office" / "no other people" to the scene bank. Must be settled in P2 prompt tuning, not discovered mid-P3.

---

## 6. Generator model set — updated reality

| Model | ComfyUI support | Weights needed | VRAM class |
|---|---|---|---|
| **Wan 2.2 T2V-A14B** | ✅ native + bundled template | 2×13.3 GiB experts + 6.3 umt5 + 0.24 VAE | ~14 GiB resident — **proven working** |
| **HunyuanVideo 1.5** | ✅ native (`HunyuanVideo15`), bundled 720p t2v template | 720p t2v is **fp16-only, 15.5 GiB** (no fp8 published); + Qwen2.5-VL-7B 8.7 fp8 + 2.35 VAE | ~16–18 GiB. 480p t2v cfg-distilled fp8 (7.76 GiB) is the light option |
| **LTX 2.3** | ✅ native (`LTXAV` class) | 22B: ~22 GiB fp8 transformer + **Gemma-3-12B** text encoder 12.3 GiB | ~34 GiB — **heaviest; least viable under contention** |

Corrections to plan §4.3: "LTX-2" is superseded by **LTX 2.3** (22B, `Comfy-Org/ltx-2.3` holds *only* LoRAs — base weights live in `Lightricks/LTX-2.3-fp8` or `Kijai/LTX2.3_comfy`). "HunyuanVideo or 1.5" → **1.5 is available and native**.

### ⚠️ Ethics landmine — do not use the LTX identity LoRAs

`Comfy-Org/ltx-2.3` ships `ltx-2.3-id-lora-celebvhq-3k` and `ltx-2.3-id-lora-talkvid-3k`, and there's a bundled `video_ltx2_3_id_lora.json` template. These are **identity LoRAs trained on CelebV-HQ / TalkVid — real people, including public figures.** Using them would directly violate plan §3.1 (synthetic identities only, no real-person likeness) and would poison the §7.4 identity-leakage gate at the source. Recommend an explicit denylist of these files in the driver so they can never be loaded accidentally.

**Recommendation:** Wan 2.2 (primary, proven) + HunyuanVideo 1.5 at 720p fp16 as model 2. Defer LTX 2.3 to a stretch goal — it is 2.4× the memory footprint of Wan for the same clip, and under current contention it's the most likely to OOM. Two solid generators with clean per-model bias analysis beats three with a flaky one.

---

## 7. Recommended P1 settings

```
model:        wan2.2_t2v_{high,low}_noise_14B_fp8_scaled  + lightx2v 4-step LoRAs (both)
resolution:   1280×720
fps:          16
frames:       81 (5.06s) primary; 121/161 for the long tail — 4k+1 required
steps:        4 total, split 2+2 at the MoE boundary
cfg:          1.0   (4-step LoRA is CFG-free — do not raise; 2× cost for nothing)
sampler:      euler / simple, shift 5.0
vae:          wan_2.1_vae.safetensors   (NOT wan2.2_vae — that's for the 5B TI2V)
output:       native CreateVideo + SaveVideo, h264 mp4 (VHS not required)
```

Pilot cost estimate: 112 clips × 142 s ≈ **4.4 GPU-hours** for the full 56-cell × 2-seed sweep at 5 s. Cheap — we can afford to iterate prompts several times in P2.

---

## 8. Open items for you

1. **GPU allocation** (§2) — blocking for P3, not for P1. Recommend 2 dedicated.
2. **Duration policy** (§3) — recommend 70/20/10 skew toward 5 s.
3. **fps handling across generators** (§5.1) — declare per-generator, or normalize?
4. **Model set** (§6) — endorse Wan 2.2 + Hunyuan 1.5, defer LTX 2.3?
5. Plan §11 items (taxonomy confirmation, I2V variant, audio, rejection-tolerance policy) remain open and are not blocked by P0.

Not started, per your instruction that no dataset generation happens before you approve the pilot matrix: the 56-cell pilot prompt matrix (kickoff item 3).
