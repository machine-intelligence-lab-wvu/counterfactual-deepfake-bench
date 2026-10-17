#!/usr/bin/env bash
# NCSA DeltaAI job: HunyuanVideo 1.5, one GH200 node (4 GPUs) per shard.
# Defaults to the 84-clip tail of the Bridges-2 sub504b run.
# Paths come from /work/nvme/.../fairdeep/env.sh (home quota cannot hold the weights).
#   for k in 0 1; do sbatch --export=ALL,SHARD=$k,NSHARDS=2 slurm/generate_hunyuan15_deltaai.sbatch; done
#   LIMIT=1 sbatch --gpus-per-node=1 --time=1:00:00 slurm/generate_hunyuan15_deltaai.sbatch  # smoke
# Resubmitting is safe - run_batch.py skips clips that already exist.
#SBATCH --job-name=fairdeep-hy15
#SBATCH --account=bjej-dtai-gh
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=64
#SBATCH --mem=400G
#SBATCH --time=16:00:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
source /work/nvme/bjej/rahamed/fairdeep/env.sh
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
MATRIX="${MATRIX:-manifests/prompt_matrix_hunyuan15_sub504b_rest.json}"
SHARD="${SHARD:-0}"
NSHARDS="${NSHARDS:-1}"
EXTRA=()
[ -n "${LIMIT:-}" ] && EXTRA+=(--limit "$LIMIT")

IDS="$("$VENV/bin/python" -c "import json,sys; s=json.load(open('$MATRIX'));
print(','.join(x['prompt_id'] for x in s[$SHARD::$NSHARDS]))")"

# per-job server logs/pids: shards on different nodes share the ComfyUI tree
export LOG_DIR="$FAIRDEEP_COMFY_ROOT/logs/${SLURM_JOB_ID:-local}"
eval "$(bash scripts/launch_comfy.sh)"
trap 'kill $(cat "$FAIRDEEP_PIDS") 2>/dev/null || true' EXIT

"$VENV/bin/python" driver/run_batch.py --matrix "$MATRIX" --model hunyuan15 \
  --hosts "$FAIRDEEP_HOSTS" --out-root "$OUT_ROOT" --steps 20 --cfg 6.0 \
  --only-ids "$IDS" "${EXTRA[@]}" \
  --log "manifests/generation_log_hunyuan15b_deltaai_s${SHARD}_${SLURM_JOB_ID:-local}.jsonl"
