#!/usr/bin/env bash
# PSC Bridges-2 job: LTX 2.3 on H100s (GPU-shared allows up to 4 GPUs per job).
# Paths come from /ocean/.../fairdeep/env.sh (home quota is too small for weights).
#   sbatch slurm/generate_ltx23_bridges2.sbatch                       # full matrix
#   LIMIT=2 sbatch --gres=gpu:h100-80:1 --time=1:00:00 slurm/generate_ltx23_bridges2.sbatch   # smoke test
# Resubmitting is safe - run_batch.py skips clips that already exist.
#SBATCH --job-name=fairdeep-ltx23
#SBATCH --account=cis260353p
#SBATCH --partition=GPU-shared
#SBATCH --gres=gpu:h100-80:4
#SBATCH --time=48:00:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
source /ocean/projects/cis260353p/rahamed/fairdeep/env.sh
mkdir -p logs
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
MATRIX="${MATRIX:-manifests/prompt_matrix_ltx23.json}"
EXTRA=()
[ -n "${LIMIT:-}" ] && EXTRA+=(--limit "$LIMIT")
[ -n "${ONLY_IDS:-}" ] && EXTRA+=(--only-ids "$ONLY_IDS")

eval "$(bash scripts/launch_comfy.sh)"
trap 'kill $(cat "$FAIRDEEP_PIDS") 2>/dev/null || true' EXIT

"$VENV/bin/python" driver/run_batch.py --matrix "$MATRIX" --hosts "$FAIRDEEP_HOSTS" \
  --out-root "$OUT_ROOT" --steps 20 --cfg 3.0 "${EXTRA[@]}" \
  --log "manifests/generation_log_${SLURM_JOB_ID:-local}.jsonl"
