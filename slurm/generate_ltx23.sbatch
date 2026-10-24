#!/usr/bin/env bash
# Example SLURM job: one node, 4 GPUs, LTX 2.3 run. Adjust partition/account/time.
# Resubmitting is safe - run_batch.py skips clips that already exist.
#SBATCH --job-name=dfbench-ltx23
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
MATRIX="${MATRIX:-manifests/prompt_matrix_ltx23.json}"
OUT_ROOT="${OUT_ROOT:-$(dirname "$PWD")/deepfake-bench-data/synthetic}"

eval "$(bash scripts/launch_comfy.sh)"
trap 'kill $(cat "$DFBENCH_PIDS") 2>/dev/null || true' EXIT

"$VENV/bin/python" driver/run_batch.py --matrix "$MATRIX" --hosts "$DFBENCH_HOSTS" \
  --out-root "$OUT_ROOT" --steps 20 --cfg 3.0 \
  --log "manifests/generation_log_${SLURM_JOB_ID:-local}.jsonl"
