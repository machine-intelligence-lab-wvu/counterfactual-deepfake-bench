# fairdeep-datagen

Controlled synthetic video generation for **FairDeep-Fake Bench**. ComfyUI is driven headlessly
over its HTTP API, one server per GPU. Clips are published to the HF dataset
[`Ahsanz/fairdeep-bench`](https://huggingface.co/datasets/Ahsanz/fairdeep-bench) (private).

## Layout
| Path | Role |
|---|---|
| `specs/taxonomy.py` | 56 demographic cells + scene/lighting/behaviour/camera banks |
| `specs/build_matrix.py` | counterfactual-group prompt matrix → `manifests/*.json` |
| `renderers/ltx23.py` | spec → LTX 2.3 positive/negative prompt |
| `workflows/ltx23_graph.py` | production ComfyUI API graph (LTX 2.3 dev bf16, audio+video) |
| `workflows/{wan22,hunyuan15,ltx23}_t2v.py` | throughput benchmarks |
| `driver/run_batch.py` | multi-GPU batch driver, resumable, writes sidecars + log |
| `qc/scan.py`, `qc/montage.py` | technical QC report, review montages |
| `scripts/` | cluster setup helpers, HF upload |
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
```
The driver skips clips whose `.mp4` already exists, so a killed job can be resubmitted.
To split one matrix across clusters, give each a different `--only-ids` list (or build a
separate matrix with different group indices) and merge on Hugging Face.

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
