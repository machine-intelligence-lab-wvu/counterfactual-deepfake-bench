#!/usr/bin/env bash
# Render one batch into one view as a Slurm array: 1 GPU (partition requires it), many CPUs.
#   sbatch --array=0-3 --export=ALL,VIEW=face512,BATCH=fake_b1,NSHARDS=4 eval/slurm/preprocess.sbatch
#SBATCH --job-name=fd-prep
#SBATCH --account=bjej-dtai-gh
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=110G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%A_%a.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source eval/env.sh
python -m eval.preprocess --view "$VIEW" --batch "$BATCH" \
  --shard "${SLURM_ARRAY_TASK_ID:-0}" --nshards "${NSHARDS:-1}" --workers "${WORKERS:-36}" \
  ${EXTRA:-}
