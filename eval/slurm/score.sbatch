#!/usr/bin/env bash
# Score one batch in one view with one detector as a Slurm array: 1 GPU, many CPUs for decode.
#   sbatch --array=0-1 --export=ALL,DETECTOR=decof,VIEW=face512,BATCH=fake_b1,NSHARDS=2 eval/slurm/score.sbatch
#SBATCH --job-name=fd-score
#SBATCH --account=bjej-dtai-gh
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=110G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x_%A_%a.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source eval/env.sh
python -m eval.run --detector "$DETECTOR" --view "$VIEW" --batch "$BATCH" \
  --shard "${SLURM_ARRAY_TASK_ID:-0}" --nshards "${NSHARDS:-1}" \
  --batch-size "${BS:-32}" --workers "${WORKERS:-64}" ${EXTRA:-}
