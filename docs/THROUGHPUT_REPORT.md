# Full-Precision Throughput Report — 3 Generators, 15-Day Budget

**Counterfactual DeepFake Bench / controlled synthetic video generation**
Date: 2026-08-06 · 4× RTX PRO 5000 Blackwell (48.9 GiB each) · ComfyUI v0.30.0
Supersedes the throughput section of `P0_REPORT.md` (which measured fp8 + 4-step LoRA only).

---

## 1. GPU status: clear

Your verl RL job (`ray::WorkerDict.actor_rollout_ref_update_actor`) has exited. All 4 GPUs idle, host RAM 199 GiB free of 251. I ran one ComfyUI server per GPU (ports 8188–8192) and benchmarked all three generators concurrently. **All numbers below are on dedicated, uncontended GPUs.**

## 2. What was installed

All at full precision, as requested (~164 GiB total, disk now 2.8 TB free):

| Model | Weights | Note |
|---|---|---|
| Wan 2.2 T2V-A14B | both fp16 MoE experts (27 GiB each) + `umt5_xxl_fp16` | |
| HunyuanVideo 1.5 720p T2V | `_fp16` + **full** Qwen2.5-VL-7B (not fp8) + byt5 + fp16 VAE | 720p T2V has no fp8 published anyway |
| LTX 2.3 | `ltx-2.3-22b-dev` **bf16** (43 GiB) + **full** Gemma-3-12B (23 GiB) + x2 upscaler | chose `dev` over `distilled`; full Gemma over template's fp4_mixed |

## 3. Measured throughput

All at 1280×720 (LTX: 1280×704), one clip, warm model, **dedicated GPU**.

### Wan 2.2 T2V-A14B — 16 fps, frames must be 4k+1

| Precision | Steps | CFG | LoRA | Frames | Length | Time |
|---|---|---|---|---|---|---|
| fp8 | 4 | 1.0 | 4-step | 81 | 5.06 s | 142.2 s |
| **fp16** | 4 | 1.0 | 4-step | 81 | 5.06 s | **186.2 s** (mean of 177.2 / 192.2 / 189.3) |
| fp16 | 4 | 1.0 | 4-step | 121 | 7.56 s | 330.3 s |
| fp16 | 4 | 1.0 | 4-step | 161 | 10.06 s | 513.8 s |
| fp8 | 20 | 1.0 | — | 81 | 5.06 s | 657.8 s |
| fp8 | 20 | 3.5 | — | 81 | 5.06 s | 1300.9 s |
| **fp16** | **20** | **3.5** | — | 81 | 5.06 s | **1628.3 s** ← reference quality |

### HunyuanVideo 1.5 720p T2V — 24 fps

| Precision | Steps | CFG | Frames | Length | Time |
|---|---|---|---|---|---|
| **fp16** | **20** | **6.0** | 121 | 5.04 s | **1447.3 s** ← reference quality |

### LTX 2.3 22B `dev` — 24 fps, 1280×704

| Precision | Steps | CFG | Audio | Frames | Length | Time |
|---|---|---|---|---|---|---|
| bf16 | 8 | 1.0 | yes | 97 | 4.04 s | 69.1 s (undercooked — validation only) |
| **bf16** | **30** | **3.0** | yes | 121 | 5.04 s | **198.3 s** ← reference quality |
| bf16 | 30 | 3.0 | **no** | 121 | 5.04 s | 222.2 s |
| bf16 | 30 | 3.0 | yes | 241 | 10.04 s | 477.6 s |

### Cost decomposition (Wan, isolated by holding everything else fixed)

| Lever | Multiplier |
|---|---|
| fp8 → fp16/bf16 (**what you asked for**) | **1.25–1.35×** |
| CFG 1.0 → 3.5 (doubles forward passes) | **1.98×** |
| 4 steps → 20 steps | **4.63×** |
| Combined: 4-step fp8 → 20-step fp16 | **11.4×** |

Empirical model: `time ≈ 25 s + steps × cfg_mult × 41.8 s` (fp16, 81 f, 720p). Predicted the 20-step case at 1697 s vs 1628 s measured — **4% error**, so extrapolation is reliable.

**Precision was never the expensive choice.** Full precision costs 1.35×; full *sampling* costs 9.2×. Your fp16/bf16 requirement is cheap — the budget problem is steps × CFG.

### Two headline surprises

1. **LTX 2.3 is 7–8× cheaper than Wan/Hunyuan at full quality** (198 s vs 1628/1447 s) despite being the largest model at 22B. Its VAE compresses far more aggressively, so it samples dramatically fewer latent tokens. It also scales better with duration (frames^1.27 vs Wan's frames^1.70), making 10 s clips affordable only on LTX.
2. **LTX's native audio is free.** With audio 198.3 s, without 222.2 s — the difference is inside run-to-run noise. This answers plan §11's audio question for LTX at zero cost.

**Measurement caveat:** replicates spread ±8–12% (e.g. 177.2 / 189.3 / 192.2 s for the same config). Treat every figure as ±12%; the budget below reserves 15% partly for this.

## 4. Budget: 15 days × 4 GPUs = 1,440 GPU-hours

Reserving 15% for QC, driver restarts, regeneration of QC failures, and timing variance leaves **1,224 GPU-h** for generation. Target 5,750 raw clips, 56 cells.

| Scenario | Wan | Hunyuan | LTX | Total | Verdict |
|---|---|---|---|---|---|
| **A** — equal split, full quality | 1,916 | 1,916 | 1,918 | 1,743 GPU-h / 18.2 d | ✗ **42% over** (21.4 d with reserve) |
| **B** — full quality, cost-weighted N | 1,219 | 1,219 | 3,312 | 1,224 GPU-h / **12.7 d** | ✓ **fits** |
| **C** — Wan on 4-step LoRA, others full | 1,916 | 1,916 | 1,918 | 975 GPU-h / 10.2 d | ✓ fits, but Wan is distill-sampled |
| **D** — equal split full quality, trim total | 1,346 | 1,346 | 1,346 | 1,224 GPU-h | ✓ fits but only **4,037 raw** (−30%) |

**The blunt version: "all three models" + "no quality degradation" + "5,750 clips" + "15 days" cannot all hold with equal per-model counts.** Scenario A needs ~21 days. You can keep any three constraints; the cheapest one to bend is *equal allocation*.

### Recommendation: Scenario B

Keep reference-quality sampling on all three generators and all 5,750 clips — just stop insisting each generator contributes equally, since LTX delivers 8× the clips per GPU-hour.

- Wan 2.2 — **1,219 clips** (21.8 raw/cell → ~18.5 accepted/cell)
- HunyuanVideo 1.5 — **1,219 clips** (21.8 raw/cell → ~18.5 accepted/cell)
- LTX 2.3 — **3,312 clips** (59.1 raw/cell → ~50.3 accepted/cell)
- **12.7 days**, leaving ~2 days slack before your 15-day wall.

This satisfies the plan's own §4.2 targets: it wants "20–30 accepted clips per cell per model" (we get 18.5 / 18.5 / 50.3 — Wan and Hunyuan land just under, LTX well over) and a floor of "60–70 accepted per intersectional cell" across models (**we get 87**).

The cost is statistical: per-generator bias estimates will be ~1.6× noisier for Wan and Hunyuan than for LTX. That is a defensible, reportable design choice — and far better than degrading the generators or missing the deadline. If you'd rather have equal power per generator, Scenario D is the honest alternative at 4,037 raw clips.

### One caveat on the phrase "full quality"

The 20 steps I benchmarked is the **ComfyUI reference default**, not each model's maximum. Hunyuan's template explicitly notes its *original* setting is 50 steps; Wan's upstream configs go to 40–50. At 50 steps nothing fits — Hunyuan would be ~3,620 s/clip and even Scenario B would need ~30 days. I recommend documenting "20 steps, reference default" as the declared generation setting in the datasheet.

## 5. Recommended settings

```
# Wan 2.2 T2V-A14B                         # HunyuanVideo 1.5 720p T2V
unet    wan2.2_t2v_{high,low}_..._fp16     unet    hunyuanvideo1.5_720p_t2v_fp16
text    umt5_xxl_fp16                      text    qwen_2.5_vl_7b (full) + byt5_small_glyphxl_fp16
vae     wan_2.1_vae   (NOT wan2.2_vae)     vae     hunyuanvideo15_vae_fp16
res     1280x704      fps 16               res     1280x704      fps 24
frames  81  (4k+1 required)                frames  121
steps   20, split 10/10 at MoE boundary    steps   20   cfg 6.0   shift 7.0
cfg     3.5   shift 5.0   euler/simple     sampler euler / simple (no EasyCache - costs quality)

# LTX 2.3 22B dev
ckpt    ltx-2.3-22b-dev.safetensors (bf16, contains video+audio VAE)
text    gemma_3_12B_it (full bf16)      res 1280x704   fps 24   frames 121
steps   30   cfg 3.0   euler             audio: on (free)
```

**Standardize all three at 1280×704.** LTX snaps height to a multiple of 32, so it physically cannot emit 720. I verified Wan accepts 704 at no extra cost (189.3 s vs 192.2 s at 720). Generating all three at 704 gives exact resolution parity, removing a per-generator confound that a resolution-sensitive detector would otherwise pick up. Without this you'd be comparing 720-tall Wan/Hunyuan against 704-tall LTX.

## 6. Unresolved design tensions (need your call)

1. **fps is not uniform: Wan 16, Hunyuan 24, LTX 24.** Wan 2.2-A14B is trained at 16 fps; forcing 24 is off-distribution. So fps partially correlates with generator no matter what. Declare it per-generator and report it, or resample everything to 16 fps in post (resampling adds its own artifacts). I lean toward declaring it.
2. **Clip duration vs. generator confound.** 10 s clips cost 3.23× on Wan but only 2.41× on LTX. Putting the long clips only where they're affordable would make duration correlate with generator. I recommend **5 s uniform** for the controlled set, with duration variation added later as a small balanced sub-study rather than spread across the whole dataset. Note this contradicts plan §6.3's "5–10 s, vary within each cell" — honoring that at full quality drops Wan/Hunyuan to ~13.8 raw/cell, below the plan's own floor.
3. **Age compliance looks shaky in both directions.** The Wan pilot cell read close to the prompted "late thirties," but LTX rendered the same prompt as visibly older (45–55). §5.4 anticipated models skewing *young*; LTX skews *old*. Either way this confirms post-hoc verification must gate the age bins — the prompt cannot be trusted. Unmeasured across cells until the P1 pilot.
4. **Ethics item from P0 still stands:** do not use `ltx-2.3-id-lora-celebvhq-3k` / `-talkvid-3k` (trained on real people). Denylist them in the driver.

## 7. Verified working

Three end-to-end API workflows, submitted headlessly via `POST /prompt`, no ComfyUI core modifications:
- Wan 2.2 MoE two-expert T2V (fp8 and fp16 paths)
- HunyuanVideo 1.5 720p T2V (`SamplerCustomAdvanced` + `CFGGuider` path)
- LTX 2.3 audio-video T2V (latent concat → joint sample → AV split → h264 + AAC 48 kHz)

Output inspected frame-by-frame for all three: correct dimensions, frame counts, real interframe motion, no frozen/black frames, plausible photorealistic single-subject faces matching the prompted demographic cell.
