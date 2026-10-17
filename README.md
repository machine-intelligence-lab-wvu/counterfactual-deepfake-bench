# fairdeep-datagen

Controlled synthetic video generation for **FairDeep-Fake Bench**. ComfyUI is driven headlessly
over its HTTP API, one server per GPU. Clips are published to the HF dataset
[`Ahsanz/fairdeep-bench`](https://huggingface.co/datasets/Ahsanz/fairdeep-bench) (private).

## Layout
| Path | Role |
|---|---|
| `specs/taxonomy.py` | 56 demographic cells + scene/lighting/behaviour/camera banks |
| `specs/build_matrix.py` | counterfactual-group prompt matrix → `manifests/*.json` |
| `specs/derive_matrix.py` | re-time a matrix for another generator (same cells, groups, seeds) |
| `renderers/{ltx23,wan22,hunyuan15}.py` | spec → per-model positive/negative prompt |
| `workflows/{ltx23,wan22,hunyuan15}_graph.py` | production ComfyUI API graphs (LTX 2.3 audio+video, Wan 2.2 and Hunyuan 1.5 video-only) |
| `workflows/{wan22,hunyuan15,ltx23}_t2v.py` | throughput benchmarks |
| `driver/run_batch.py` | multi-GPU batch driver, resumable, writes sidecars + log |
| `qc/scan.py`, `qc/montage.py` | technical QC report, review montages |
| `scripts/` | cluster setup helpers, remaining-work matrix, HF upload |
| `slurm/` | example SLURM job |
| `P0_REPORT.md`, `THROUGHPUT_REPORT.md` | feasibility + timing reports |

## New cluster
```bash
mkdir fairdeep && cd fairdeep
git clone git@github.com:Ahsan06080/fairdeep-datagen.git
cd fairdeep-datagen
hf auth login                     # LTX 2.3 / Gemma weights come from HF
bash setup.sh                     # ComfyUI @ pinned commit, venv, LTX weights (~67 GiB)
# MODELS=all bash setup.sh        # also Wan 2.2 + HunyuanVideo 1.5 (~200 GiB)
```
Defaults put `ComfyUI/` and `.venv/` next to this repo. Override with `FAIRDEEP_COMFY_ROOT`,
`VENV`, `TORCH_INDEX` (CUDA wheel index; default cu128) and `HF_HUB_CACHE`.

## Generate
```bash
# interactive node
eval "$(bash scripts/launch_comfy.sh)"            # one server per GPU, exports FAIRDEEP_HOSTS
../.venv/bin/python driver/run_batch.py --matrix manifests/prompt_matrix_ltx23.json \
    --hosts "$FAIRDEEP_HOSTS" --out-root ../fairdeep-bench/synthetic --steps 20 --cfg 3.0
kill $(cat "$FAIRDEEP_PIDS")

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
../.venv/bin/python qc/scan.py --root ../fairdeep-bench/synthetic --out-dir manifests
../.venv/bin/python scripts/upload_hf.py                 # rebuild metadata.csv + upload new clips
hf download Ahsanz/fairdeep-bench --repo-type dataset --local-dir ../fairdeep-bench
```

## Pinned versions
ComfyUI `7972b5ba`, VideoHelperSuite `4ee72c06`, torch 2.11.0+cu128, Python 3.12.

## Ethics guardrails
Synthetic identities only. `workflows/ltx23_graph.py` refuses identity LoRAs trained on real
people (CelebV-HQ / TalkVid). Every sidecar records `ai_generated: true`.
