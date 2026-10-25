# Counterfactual DeepFake Bench — Synthetic Video Generation: Overview & Progress

Source material for a presentation. Everything here is measured from the `counterfactual-deepfake-bench`
repository (all branches), its run logs and its QC reports, as of **2026-10-18**.

---

## 1. What was built and why

A **controlled synthetic video corpus** for studying demographic bias in deepfake / AI-generated-
video detection. The premise: on found datasets (CelebDF, FaceForensics++, DFDC), demographics are
tangled up with capture conditions — camera, lighting, venue, video quality all differ
systematically between demographic groups, so any measured "bias" could be an artifact of how the
footage was collected. Generating the corpus instead makes **demographic presentation the only
deliberately varied factor**, with every nuisance factor held fixed or balanced by construction.

Three text-to-video generators, one shared prompt design, one shared taxonomy.

**Headline numbers**

| | |
|---|---|
| Clips generated | **4,536** |
| Clips passing QC | **3,936** |
| Generators | 3 (LTX 2.3, Wan 2.2, HunyuanVideo 1.5) |
| Demographic cells | 56 (7 race × 2 gender × 4 age) |
| Counterfactual groups | 36 (LTX, Wan) · 9 so far (Hunyuan) |
| GPU-hours | **≈ 409** |
| Generation failures | **0** |
| Compute sites | 3 (local Blackwell box, PSC Bridges-2, NCSA DeltaAI) |
| Video spec | 1280×704 h264, 5.0–6.1 s per clip |

---

## 2. The demographic taxonomy — 56 cells

Chosen to be **FairFace-compatible**, so that FairFace/MiVOLO classifiers can later verify the
output and so results line up with prior per-subgroup detector studies.

- **7 race / ethnicity presentations:** White, Black, East Asian, Southeast Asian, South Asian,
  Middle Eastern, Hispanic
- **2 gender presentations:** man, woman
- **4 age bands:** 18-29, 30-44, 45-59, 60+

**7 × 2 × 4 = 56 intersectional cells.**

An important framing point for the talk: these encode **perceived demographic presentation, not
self-identified identity** — synthetic people have no self-identification. The paper and datasheet
need to say this explicitly.

---

## 3. The core design idea — the counterfactual group

This is the methodological centrepiece and deserves its own slide.

**A counterfactual group is one content recipe, instantiated across all 56 demographic cells with
a shared random seed.** The group fixes:

- the setting (e.g. open-plan office)
- the lighting condition (e.g. flat overcast daylight)
- the behaviour (e.g. smile → nod → head tilt)
- the camera mode (static or slow handheld sway)
- the clothing item
- the clip duration

…and then only the demographic description changes across the 56 clips in that group.

```
clips = groups × 56 cells
36 groups × 56 cells = 2,016 clips per generator
```

**Why it matters:** balance is *structural*, not sampled. Because every cell appears exactly once in
every group, every cell automatically sees a bit-identical distribution of settings, lighting,
behaviours, camera moves and durations. No Latin square, no random assignment, no post-hoc
reweighting — and nothing can silently drift out of balance.

### What a counterfactual pair actually looks like

Same group (g000), same seed `1191460415117186840`, same office / overcast / smile / static camera /
knit sweater / 145 frames. The **only** difference is the demographic clause:

> Photorealistic documentary video portrait of **a White man in his early thirties, faint expression
> lines, healthy adult skin, with short brown hair**, wearing a plain knit sweater. **He** is
> beginning with a neutral expression, then breaking into a wide smile as the cheeks lift and the
> eyes crease, followed by two clear nods and a small head tilt. Continuous natural movement
> throughout the entire shot… Background: a modern open-plan office, softly blurred behind the
> subject. Lighting: flat even overcast daylight. static camera, head-and-shoulders portrait
> framing, face centred…

> Photorealistic documentary video portrait of **a Black woman in her late sixties, clearly elderly,
> deeply wrinkled and creased skin, age spots, sagging jawline, hooded eyelids, thinning skin, with
> short grey coiled hair**, wearing a plain knit sweater. **She** is beginning with a neutral
> expression, then breaking into a wide smile… *(remainder byte-identical)*

---

## 4. How the stratification is actually produced

`specs/build_matrix.py` builds the matrix. The mechanics, in order:

**4.1 Deterministic seeds.** Every seed is a blake2b hash of the spec fields — no `random()`, no
global state. The same matrix rebuilds bit-identically on any machine, and one seed is shared by
all 56 cells of a group.

**4.2 Balanced assignment of content to groups.** For each factor, a balanced list
`[i % n_levels for i in range(groups)]` is built and then shuffled by a Fisher-Yates driven by a
stable per-field hash. This was a deliberate fix: **modular strides (`g * k % n`) are a trap** —
whenever `gcd(k, n) > 1` they cover only `n/gcd` levels, silently dropping bank entries. A real bug
of exactly this kind, `(g*3) % 6` on lighting, had dropped *backlit* and *low-light* — the two
conditions the study most needs. Independent shuffles also keep the factors decorrelated from each
other.

**4.3 Lighting × duration are balanced jointly, not independently.** Both are technical factors a
detector is sensitive to, and lighting × skin tone is the key interaction, so they must stay
orthogonal. Independent shuffling had left low-light skewed toward short clips.

**4.4 Build-time assertions.** The builder refuses to emit a matrix unless:
- all 56 cells exist with identical counts
- every cell has an identical distribution of setting, lighting, behaviour and duration
- every bank level actually appears (coverage, not just balance)
- no bank's marginal is skewed more than 2:1
- lighting × duration combinations are within 1.5:1 of each other

**4.5 Age and hair are coupled on purpose.** Age phrasing is deliberately heavy-handed for older
bands because video models under-comply with age prompts. Hair is tiered by age band so colour
agrees with age — otherwise the prompt self-conflicts ("grey hair … with wavy black hair"). Age
detail carries **skin and bone structure only, never hair colour**, so the two never contradict.

### The content banks

| Bank | Levels | Values |
|---|---|---|
| Setting | 10 | office, plain wall, living room, library, cafe, corridor, studio, kitchen, classroom, lobby |
| Lighting | 6 | soft window, overcast, warm lamp, harsh overhead, backlit, low-light |
| Behaviour | 8 | speak, smile, listen, turn, laugh, read, think, pause |
| Attire | 6 | plain shirt, knit sweater, t-shirt, button-down, blouse, zip-up jacket |
| Camera | 2 | static, slow handheld sway |
| Duration | 2 | ~5.0 s, ~6.0 s |

**Design rule for the banks:** nothing culturally or socioeconomically marked, and every entry must
be plausibly assignable to every demographic cell. That rule is what keeps the scene from encoding
the demographic.

### Resulting balance across the 36 groups

| Factor | Distribution over 36 groups |
|---|---|
| Lighting | exactly **6 groups each** for all 6 conditions |
| Camera | **18 / 18** static / sway |
| Duration | **18 / 18** short / long |
| Setting | 3–4 groups each across 10 settings |
| Behaviour | 4–5 groups each across 8 behaviours |

Each of those group-level counts is multiplied by 56 at the clip level, and every demographic cell
sees the identical distribution.

### The 36 content recipes (useful as a backup slide)

| g | setting | lighting | behaviour | camera | frames |
|---|---|---|---|---|---|
| 0 | office | overcast | smile | static | 145 |
| 1 | cafe | backlit | listen | sway | 145 |
| 2 | lobby | lowlight | think | static | 145 |
| 3 | classroom | overcast | turn | static | 121 |
| 4 | kitchen | lowlight | turn | sway | 145 |
| 5 | livingroom | backlit | think | sway | 121 |
| 6 | office | harsh | speak | sway | 121 |
| 7 | library | lowlight | speak | static | 121 |
| 8 | studio | lowlight | listen | sway | 121 |
| 9 | classroom | harsh | laugh | sway | 121 |
| 10 | corridor | overcast | turn | sway | 145 |
| 11 | livingroom | softwindow | listen | static | 121 |
| 12 | library | backlit | listen | sway | 121 |
| 13 | plainwall | softwindow | pause | sway | 121 |
| 14 | livingroom | warmlamp | smile | static | 121 |
| 15 | cafe | overcast | speak | static | 121 |
| 16 | classroom | softwindow | speak | sway | 145 |
| 17 | studio | backlit | think | static | 121 |
| 18 | library | backlit | laugh | static | 145 |
| 19 | plainwall | overcast | read | static | 145 |
| 20 | corridor | softwindow | speak | static | 145 |
| 21 | kitchen | overcast | pause | static | 121 |
| 22 | corridor | backlit | laugh | sway | 145 |
| 23 | cafe | warmlamp | read | sway | 121 |
| 24 | plainwall | lowlight | read | sway | 145 |
| 25 | studio | softwindow | smile | static | 121 |
| 26 | lobby | harsh | think | sway | 145 |
| 27 | plainwall | softwindow | pause | sway | 145 |
| 28 | library | lowlight | laugh | sway | 121 |
| 29 | office | harsh | turn | sway | 145 |
| 30 | corridor | warmlamp | listen | static | 145 |
| 31 | kitchen | harsh | read | sway | 121 |
| 32 | livingroom | warmlamp | smile | static | 121 |
| 33 | cafe | harsh | pause | static | 145 |
| 34 | office | warmlamp | smile | static | 145 |
| 35 | lobby | warmlamp | turn | static | 145 |

*(Hunyuan's 504 completed clips are groups 2, 8, 14, 16, 18, 19, 21, 23, 29 of this same table.)*

---

## 5. From spec to prompt

A **renderer** turns each spec into generator-specific prompt text. The LTX renderer follows LTX
2.3's own prompting guidance — actions as they occur over time, explicit visual detail, then audio —
producing an Action / Visual / Audio-shaped dense prose prompt.

Prompt skeleton:
1. **Subject + demographic** (the controlled variable): race phrase, gender word, age phrase, age
   skin/structure detail, hair, attire
2. **Core action over time**: the behaviour as a sequence of events, plus a motion clause
3. **Visual detail**: background, lighting, framing, "single person alone in the frame", skin
   texture, camera
4. **Audio** (LTX only): the behaviour's matching sound

**Cross-generator prompt matching:** the Wan and Hunyuan renderers are literally *the LTX prompt
minus its audio sentence*, with the same negative prompt — so the generator is the only variable
between arms.

**The negative prompt** carries the crowd terms (multiple people, background people, extra faces,
second person, reflection of a person, poster of a face), anatomy and artifact terms, style terms
(cartoon, anime, 3d render, plastic waxy skin), and stillness terms (static frozen image, rigid
face, slideshow, single held pose).

Two empirical findings worth a slide, because they are counter-intuitive:

- **Naming an artifact can inject it.** Adding pillarbox / letterbox / "black bars" terms to the
  negative prompt made pillarboxing markedly *worse* (411–739 dark columns vs 328–336 without).
  Negation is unreliable through a text encoder.
- **The stillness terms are load-bearing.** 3 of the first 12 pilot samples came out effectively
  frozen; the motion clause and stillness negatives are what fixed it.

### Prompt development history (the pilots)

Before the main run, ~32 pilot clips were generated across named experiments visible in the repo:

| Pilot | What it tested |
|---|---|
| `sample` (12 clips) | first end-to-end demographic sweep |
| `motionfix` (3) | rewriting behaviours from *states* to *event sequences* |
| `v2test` (8) / `v3test` (3) | prompt revisions on the weakest cells |
| `seedtest` (3) | whether a failure was seed-specific |
| `setswap` (3) | whether a failure was scene-specific |
| `cleancombo` (3) | a cleaned prompt combination |

**The biggest single fix:** behaviours were originally written as states ("smiling and nodding
slowly") and produced near-frozen clips — inter-frame motion **0.09–0.24**. Rewriting every
behaviour as an explicit sequence of at least two resolving movements lifted that to **2.4–4.2**.
`smile` remained weakest (still 27 % frozen in one group), so it was rewritten again to *open* with
head movement rather than an expression change.

---

## 6. The three generators

All weights at full precision; all output standardized to **1280×704**. (LTX snaps height to a
multiple of 32 and physically cannot emit 720; Wan accepts 704 at no extra cost. Generating all
three at 704 gives exact resolution parity and removes a per-generator confound.)

| | **LTX 2.3 22B `dev`** | **Wan 2.2 T2V-A14B** | **HunyuanVideo 1.5 720p** |
|---|---|---|---|
| Precision | bf16 | fp16 | fp16 |
| Sampling | 20 steps, cfg 3.0 | 4 steps, cfg 1.0 + lightx2v distill LoRA | 20 steps, cfg 6.0, shift 7 |
| Sampler | euler / simple | euler / simple, shift 5.0 | euler / simple |
| Architecture note | joint audio+video latents, sampled together then split | MoE: high-noise expert then low-noise expert on one schedule | Qwen2.5-VL-7B + byT5 dual text encoder |
| Text encoder | Gemma-3-12B (full bf16) | umt5-xxl fp16 | Qwen2.5-VL-7B + byT5 |
| VAE | in-checkpoint (video + audio) | wan_2.1_vae (*not* 2.2 — that's the 5B model) | hunyuanvideo15_vae_fp16 |
| fps | 24 | 16 (native; 24 would be off-distribution) | 24 |
| Frames | 121 / 145 (stride 8k+1) | 81 / 97 (stride 4k+1) | 121 / 145 (stride 4k+1) |
| Duration | 5.04 / 6.04 s | 5.06 / 6.06 s | 5.04 / 6.04 s |
| Audio | **yes**, native, 48 kHz AAC | no | no |

**Cost finding that drove the model plan:** at reference quality, 5 s at 1280×704 costs
**LTX 198 s/clip, Hunyuan 1,447 s/clip, Wan 1,628 s/clip.** LTX is 7–8× cheaper *despite being the
largest model at 22B*, because its VAE compresses far more aggressively and it therefore samples
far fewer latent tokens. It also scales better with duration (frames^1.27 vs Wan's frames^1.70).
Decomposing the cost on Wan: full precision costs only **1.25–1.35×**, raising cfg from 1.0 to 3.5
costs **1.98×**, and 4 → 20 steps costs **4.63×**. **Precision was never the expensive choice;
sampling was.** That is why Wan was run on the 4-step distill path while LTX and Hunyuan ran at
reference quality.

---

## 7. The generation pipeline

```
specs/taxonomy.py          56 cells + content banks
        │
specs/build_matrix.py      counterfactual-group matrix + balance assertions
        │                  → manifests/prompt_matrix_<model>.json
specs/derive_matrix.py     re-time the same matrix for another generator
        │                  (same cells, groups, content, seeds; new fps/frame count)
renderers/<model>.py       spec → positive + negative prompt text
        │
workflows/<model>_graph.py prompt → ComfyUI API graph (JSON node graph)
        │
driver/run_batch.py        multi-GPU batch driver
        │                  POST /prompt → poll /history → move .mp4 → write sidecar
        ▼
 output tree + .json sidecars + generation_log.jsonl
        │
qc/scan.py --faces         technical QC + face gate → qc_report.csv, cell_summary.csv
        │
scripts/upload_hf.py       flatten to metadata.csv + upload to Hugging Face
```

**Driver properties worth mentioning:**
- ComfyUI is driven **headlessly over its HTTP API**, one server per GPU, with **ComfyUI core
  unmodified** — no forked nodes to maintain.
- One worker thread per server pulls from a shared queue, so GPUs stay saturated.
- **Idempotent by `prompt_id`**: if the `.mp4` exists, skip. A killed job is simply resubmitted.
- Every attempt — success or failure — is appended to a JSONL log.
- `scripts/remaining.py` subtracts completed clips from a matrix, for the case where a run moves to
  a *different cluster* whose output tree is empty and whose skip-if-exists check therefore can't
  help.
- Shards take every Nth spec, so a shard killed early still leaves whole counterfactual groups
  rather than a demographically skewed fragment.

**Provenance — every clip ships a sidecar `.json` containing:** the full spec, the exact rendered
positive and negative prompt text, sampler / steps / cfg / scheduler, checkpoint and text-encoder
filenames, a `sha256head64m` hash of the checkpoint, the host that rendered it, wall-clock seconds,
UTC timestamp, and the provenance block `ai_generated: true`, `synthetic_identity: true`,
`real_person_depicted: false`.

**Pinned environment:** ComfyUI `7972b5ba` (v0.30.0), VideoHelperSuite `4ee72c06`,
torch 2.11.0+cu128, Python 3.12. Weights (~200 GiB across all three models) are pulled per cluster
from Hugging Face and never committed.

---

## 8. Progress

| | **LTX 2.3** | **Wan 2.2** | **Hunyuan 1.5** | **Total** |
|---|---|---|---|---|
| Groups done | **36 / 36** | **36 / 36** | **9 / 36** | |
| Clips | **2,016** | **2,016** | **504** | **4,536** |
| Accepted after QC | 1,878 | 1,566 | 492 | **3,936** |
| Mean s/clip | 159.6 | 199.2 | 1,485.9 | |
| GPU-hours | 89.4 | 111.6 | 208.4 | **409.4** |
| Failures | 0 | 0 | 0 | **0** |
| Dates | 2026-08-06 → 08-07 | 2026-10-11 → 10-13 | 2026-10-14 → 10-17 | |
| Where | local 4× RTX PRO 5000 | local 4× RTX PRO 5000 | Bridges-2 + DeltaAI | |

**Completion: LTX 100 %, Wan 100 %, Hunyuan 25 %. Overall 4,536 of a 6,048-clip three-generator
target = 75 %.**

### Timeline
- **2026-08-06** — environment recon and feasibility study; three generators benchmarked
  end-to-end on the local box; throughput and budget study.
- **2026-08-06 → 08-07** — LTX 2.3 full run: 2,016 clips in **22.3 h wall-clock** on 4 GPUs
  (39.9 s/clip wall, 159.7 s/clip per GPU).
- **2026-10-11 → 10-13** — Wan 2.2 full run: 2,016 clips, resumed across sessions.
- **2026-10-13/14** — Hunyuan generator added, matrix derived, split into two disjoint 9-group
  subsets so they could run on different clusters.
- **2026-10-14 → 10-15** — **PSC Bridges-2** (4× L40S): 420 of 504 clips as two sharded jobs,
  stopped by a 23.5 h wall-clock limit with nothing failed. The allocation was down to ~10 of
  200 SU at ~0.45 SU/clip.
- **2026-10-16** — **NCSA DeltaAI** (4× GH200): the remaining 84 clips (group 23 tail + all of
  group 29) in ~2 h 53 m per shard. Subset complete at 504/504.
- **2026-10-17** — QC of all 504 Hunyuan clips.

**Hardware comparison measured along the way:** GH200 **955 s/clip** vs L40S **1,591 s/clip** —
a 1.67× difference on identical work.

**Not yet run:** the second prepared Hunyuan subset (`sub504`, groups 1, 7, 9, 10, 11, 17, 27, 31,
34) and the remaining 18 groups — 1,512 clips, roughly 400–620 GPU-hours depending on hardware.

---

## 9. Quality control

`qc/scan.py` runs model-free technical QC immediately after generation; `--faces` adds an OpenCV
YuNet face gate. Expected resolution, fps, frame count and audio presence are read **per clip from
its own sidecar**, so each generator is checked against its own spec rather than one global
expectation.

**Technical checks:** container conformance (resolution, fps, frame count, audio track presence),
frozen clips (mean inter-frame difference < 0.30), black frames, stalled frames, pillarboxing and
letterboxing.

**Face gate:** YuNet on 8 evenly sampled frames; the largest face per frame is the subject; a
secondary face counts only if it does not overlap the subject, scores ≥ 0.75 and appears in at
least one sampled frame. Thresholds were calibrated by eye on 16 clips — decor and poster faces
topped out at 0.70–0.71, real background people scored 0.80–0.90.

**A measurement-design detail worth a slide:** motion is reported two ways. `motion_raw` (mean
absolute inter-frame pixel difference) is luminance-dependent, so it under-reports movement on
darker faces and in dim scenes — which would **manufacture a demographic bias out of a metric
artifact**. `motion_norm` divides by frame contrast to give a brightness-independent figure. Both
are reported, and conclusions require both.

### QC results

| | LTX 2.3 | Wan 2.2 | Hunyuan 1.5 |
|---|---|---|---|
| n | 2,016 | 2,016 | 504 |
| Technical pass | 1,885 — **93.5 %** | 2,016 — **100 %** | 504 — **100 %** |
| Face gate pass | 2,009 — **99.7 %** | 1,566 — **77.7 %** | 492 — **97.6 %** |
| **Accepted** | **1,878 — 93.2 %** | **1,566 — 77.7 %** | **492 — 97.6 %** |
| Accepted per cell | 30–36 (mean 33.5) | 24–32 (mean 28.0) | 7–9 (mean 8.8) |

**3,936 accepted clips → 70.3 accepted per intersectional cell across the three generators.**

**The failure modes are scene-driven, not demographic:**
- LTX pillarboxing — 107 clips, concentrated in cafe (42), classroom (47), library (11).
- Wan background people — 450 clips (22 %), concentrated in office (194), cafe (135), lobby (46).
  Wan's office acceptance is 0.13.
- Hunyuan — only 12 flagged, 7 of them one group's studio scene text inducing a second person
  regardless of demographic.

**And the design absorbs it:** because every cell appears once per group, rejecting a scene removes
it from all 56 cells equally. Acceptance by demographic stays nearly flat — LTX 0.90–0.96 across
races, Wan 0.75–0.80, Hunyuan 0.94–0.99; gender within 2 points on every generator.

---

## 10. Output and distribution

Per clip: `<model>/<cell>/<model>__<cell>__g<NNN>.mp4` plus a matching `.json` sidecar.
Published to the private Hugging Face dataset **`Ahsanz/fairdeep-bench`**, with a flat
`metadata.csv` at the root carrying one row per clip — file name, prompt_id, model, cell, race,
gender, age band, counterfactual group, setting, lighting, camera, behaviour, hair, attire, seed,
resolution, fps, duration, steps, cfg, checkpoint, timestamp, the full positive and negative prompt
text, and the merged QC columns. Upload is resumable and incremental, so new runs append.

---

## 11. Ethics guardrails built into the pipeline

- **Synthetic identities only.** No real person is depicted, and no identity conditioning is used.
- **Hard denylist in code.** The LTX ecosystem ships identity LoRAs trained on CelebV-HQ and
  TalkVid — real people, including public figures. Loading one would both violate the
  synthetic-identity rule and poison any identity-leakage analysis at the source. The graph builder
  refuses them by filename.
- **Every clip is self-declaring.** `ai_generated: true`, `synthetic_identity: true`,
  `real_person_depicted: false`, plus project and research-purpose fields, in every sidecar and
  every metadata row.
- **Perceived, not self-identified.** The taxonomy is documented as encoding perceived demographic
  presentation.

---

## 12. Suggested slide order

1. Problem — demographics are confounded with capture conditions in found deepfake datasets
2. Approach — generate the corpus; make demographics the only varied factor
3. The 56-cell taxonomy
4. The counterfactual group (with the two side-by-side prompts from §3)
5. How balance is guaranteed — structural, plus the build-time assertions
6. The content banks and the resulting 36-group balance
7. Prompt construction, and the two counter-intuitive findings (negation injects artifacts;
   behaviours must be event sequences)
8. The three generators and the cost finding (LTX 8× cheaper despite being largest)
9. The pipeline diagram and provenance/reproducibility properties
10. Progress table + timeline, including the three-cluster story
11. QC results, and why rejection is scene-correlated rather than demographic
12. Ethics guardrails
13. What remains — the Hunyuan tail
