#!/usr/bin/env bash
# HunyuanVideo 1.5 run, one node (4 GPUs) per shard. Adjust partition/account/time.
#   for k in 0 1; do sbatch --export=ALL,SHARD=$k,NSHARDS=2 slurm/generate_hunyuan15.sbatch; done
# Shard k takes every NSHARDS-th spec starting at k, so shards are balanced across
# cells and clip lengths. Resubmitting is safe - run_batch.py skips existing clips.
#SBATCH --job-name=dfbench-hy15
#SBATCH --nodes=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=32
#SBATCH --mem=200G
#SBATCH --time=48:00:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
VENV="${VENV:-$(dirname "$PWD")/.venv}"
MATRIX="${MATRIX:-manifests/prompt_matrix_hunyuan15.json}"
OUT_ROOT="${OUT_ROOT:-$(dirname "$PWD")/deepfake-bench-data/synthetic}"
SHARD="${SHARD:-0}"
NSHARDS="${NSHARDS:-1}"

IDS="$("$VENV/bin/python" -c "import json,sys; s=json.load(open('$MATRIX'));
print(','.join(x['prompt_id'] for x in s[$SHARD::$NSHARDS]))")"

eval "$(bash scripts/launch_comfy.sh)"
trap 'kill $(cat "$DFBENCH_PIDS") 2>/dev/null || true' EXIT

"$VENV/bin/python" driver/run_batch.py --matrix "$MATRIX" --model hunyuan15 \
  --hosts "$DFBENCH_HOSTS" --out-root "$OUT_ROOT" --steps 20 --cfg 6.0 \
  --only-ids "$IDS" \
  --log "manifests/generation_log_hunyuan15_s${SHARD}_${SLURM_JOB_ID:-local}.jsonl"
