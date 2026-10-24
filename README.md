# DeepFake Bench

Code for **DeepFake Bench**, a controlled benchmark of AI-generated talking-head video for
measuring how video deepfake detectors perform per demographic subgroup. This repo holds the
whole pipeline: the prompt matrix, synthetic generation, the real half, QC, and the detector
evaluation.

**Dataset:** [`machine-intelligence-lab-wvu/deepfake-bench`](https://huggingface.co/datasets/machine-intelligence-lab-wvu/deepfake-bench)
on Hugging Face (CC BY-NC 4.0): 7,056 synthetic clips from LTX 2.3, Wan 2.2, HunyuanVideo 1.5 and
LTX 2.5 across 56 demographic cells and 36 counterfactual groups, with sidecars, `metadata.csv`
and QC verdicts. The real half (CelebV-HQ) is not redistributed.

## Layout
| Path | Role |
|---|---|
| `specs/` | taxonomy (56 cells + scene/lighting/behaviour/camera banks), prompt-matrix builder, per-generator re-timing |
| `renderers/` | spec → per-model positive/negative prompt (LTX 2.3/2.5, Wan 2.2, HunyuanVideo 1.5, Kandinsky 6) |
| `workflows/` | production ComfyUI API graphs and throughput benchmarks |
| `driver/` | `run_batch.py` (multi-GPU ComfyUI driver, resumable) and `run_diffusers.py` (diffusers models, e.g. Kandinsky 6) |
| `qc/` | technical QC report and review montages |
| `real/` | the real half: fetch CelebV-HQ (or DFDC) and conform it to the synthetic spec - see `real/README.md` |
| `eval/` | detector evaluation: views, detector adapters, scoring, metrics, generator benchmark - see `eval/README.md` |
| `manifests/` | prompt matrices, generation logs and QC reports for every run |
| `results/` | evaluation snapshots (CSV tables, figures), sanity checks against published numbers |
| `scripts/` | cluster setup, remaining-work matrix, HF upload, GPU budget |
| `slurm/` | SLURM jobs (generic, PSC Bridges-2, NCSA DeltaAI) |
| `docs/` | evaluation plan, feasibility and throughput reports, presentation pack |

Generated media and weights never go into git: clips live on Hugging Face, and paths outside
the repo are set by environment variables (`DFBENCH_*`) or command-line flags.

# Generation

## New cluster
```bash
mkdir dfbench && cd dfbench
git clone https://github.com/machine-intelligence-lab-wvu/deepfake-bench.git
cd deepfake-bench
hf auth login                     # LTX 2.3 / Gemma weights come from HF
bash setup.sh                     # ComfyUI @ pinned commit, venv, LTX weights (~67 GiB)
# MODELS=all bash setup.sh        # also Wan 2.2 + HunyuanVideo 1.5 (~200 GiB)
```
Defaults put `ComfyUI/` and `.venv/` next to this repo. Override with `DFBENCH_COMFY_ROOT`,
`VENV`, `TORCH_INDEX` (CUDA wheel index; default cu128) and `HF_HUB_CACHE`.

## Generate
```bash
# interactive node
eval "$(bash scripts/launch_comfy.sh)"            # one server per GPU, exports DFBENCH_HOSTS
../.venv/bin/python driver/run_batch.py --matrix manifests/prompt_matrix_ltx23.json \
    --hosts "$DFBENCH_HOSTS" --out-root ../deepfake-bench-data/synthetic --steps 20 --cfg 3.0
kill $(cat "$DFBENCH_PIDS")

# SLURM
sbatch slurm/generate_ltx23.sbatch               # MATRIX=..., OUT_ROOT=... to override
for k in 0 1; do sbatch --export=ALL,SHARD=$k,NSHARDS=2 slurm/generate_hunyuan15.sbatch; done
```
Shard `k` takes every `NSHARDS`-th spec, so shards stay balanced across cells and clip
lengths. `slurm/*_bridges2.sbatch` are the PSC Bridges-2 variants (L40S or H100, paths
from `/ocean/.../fairdeep/env.sh` because the home quota cannot hold the weights).
`slurm/generate_hunyuan15_deltaai.sbatch` is the NCSA DeltaAI variant (4x GH200 per node,
paths from `/work/nvme/.../fairdeep/env.sh`; `MODELS=hunyuan15 bash setup.sh` is enough
for it, ~35 GiB).
The driver skips clips whose `.mp4` already exists, so a killed job can be resubmitted.
To split one matrix across clusters, give each a different `--only-ids` list (or build a
separate matrix with different group indices) and merge on Hugging Face.

### Finishing a run on another cluster
A cluster that picks up the tail of a run has an empty output tree, so it cannot skip
what is already done - give it a matrix of only the missing specs, built from the run
logs committed here:
```bash
python scripts/remaining.py --matrix manifests/prompt_matrix_hunyuan15_sub504b.json \
    --logs 'manifests/generation_log_hunyuan15b_s*.jsonl' \
    --out manifests/prompt_matrix_hunyuan15_sub504b_rest.json
MODELS=all bash setup.sh                       # Hunyuan 1.5 weights, ~200 GiB
MATRIX=manifests/prompt_matrix_hunyuan15_sub504b_rest.json sbatch slurm/generate_hunyuan15.sbatch
```
Keep `--steps 20 --cfg 6.0` and the pinned ComfyUI commit: the seed is carried in the
spec, so the same spec reproduces on any cluster only if sampler settings match. Clips
from both halves land in the same `synthetic/hunyuan15/<cell>/` layout and merge on
Hugging Face by filename.

New matrix: `python specs/build_matrix.py --model ltx23 --groups 36 --out manifests/<name>.json`

## QC and publish
```bash
../.venv/bin/python qc/scan.py --root ../deepfake-bench-data/synthetic --out-dir manifests
../.venv/bin/python scripts/upload_hf.py --repo <user>/deepfake-bench   # rebuild metadata.csv + upload new clips
hf download Ahsanz/fairdeep-bench --repo-type dataset --local-dir ../deepfake-bench-data
```
`upload_hf.py` keeps the hub's existing `metadata.csv` rows for clips this machine does not
hold, so a cluster with only its own run can append without erasing the rest.

## Pinned versions
ComfyUI `7972b5ba`, VideoHelperSuite `4ee72c06`, torch 2.11.0+cu128, Python 3.12.

## Ethics guardrails
Synthetic identities only. `workflows/ltx23_graph.py` refuses identity LoRAs trained on real
people (CelebV-HQ / TalkVid). Every sidecar records `ai_generated: true`.

# Real half
CelebV-HQ clips are fetched, filtered (single frontal face, no cuts), labelled with FairFace,
stratified per cell and conformed to the synthetic format (1280x704, 24 and 16 fps renders).
See `real/README.md`.

# Evaluation
Every clip is scored once per detector and view, and all tables are aggregated from those
scores. Four detectors are wired in (DeCoF, DeMamba, D3, V-PVP), each checked against its
published numbers in `results/sanity/`. See `eval/README.md` and `docs/EVALUATION_PLAN.md`.
