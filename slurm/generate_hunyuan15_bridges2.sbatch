#!/usr/bin/env bash
# PSC Bridges-2 job: HunyuanVideo 1.5 on the second 504-clip subset (groups
# 2,8,14,16,18,19,21,23,29 - disjoint from sub504's 1,7,9,10,11,17,27,31,34).
# Paths come from /ocean/.../fairdeep/env.sh (home quota is too small for weights).
#   sbatch slurm/generate_hunyuan15_bridges2.sbatch                         # 4x L40S
#   sbatch --gres=gpu:h100-80:4 slurm/generate_hunyuan15_bridges2.sbatch    # 4x H100 (2 SU/GPU-h)
#   LIMIT=1 sbatch --gres=gpu:l40s-48:1 --time=1:00:00 slurm/generate_hunyuan15_bridges2.sbatch  # smoke
#   for k in 0 1; do sbatch --export=ALL,SHARD=$k,NSHARDS=2 slurm/generate_hunyuan15_bridges2.sbatch; done
# Resubmitting is safe - run_batch.py skips clips that already exist.
#SBATCH --job-name=dfbench-hy15
#SBATCH --account=cis260353p
#SBATCH --partition=GPU-shared
#SBATCH --gres=gpu:l40s-48:4
#SBATCH --time=48:00:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
source /ocean/projects/cis260353p/rahamed/fairdeep/env.sh
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
MATRIX="${MATRIX:-manifests/prompt_matrix_hunyuan15_sub504b.json}"
SHARD="${SHARD:-0}"
NSHARDS="${NSHARDS:-1}"
EXTRA=()
[ -n "${LIMIT:-}" ] && EXTRA+=(--limit "$LIMIT")

IDS="$("$VENV/bin/python" -c "import json,sys; s=json.load(open('$MATRIX'));
print(','.join(x['prompt_id'] for x in s[$SHARD::$NSHARDS]))")"

eval "$(bash scripts/launch_comfy.sh)"
trap 'kill $(cat "$DFBENCH_PIDS") 2>/dev/null || true' EXIT

"$VENV/bin/python" driver/run_batch.py --matrix "$MATRIX" --model hunyuan15 \
  --hosts "$DFBENCH_HOSTS" --out-root "$OUT_ROOT" --steps 20 --cfg 6.0 \
  --only-ids "$IDS" "${EXTRA[@]}" \
  --log "manifests/generation_log_hunyuan15b_s${SHARD}_${SLURM_JOB_ID:-local}.jsonl"
