#!/usr/bin/env bash
# Aggregate every scored batch for one detector into snapshots for the given views.
#   sbatch --export=ALL,DETECTOR=decof,VIEWS="native face512" eval/slurm/aggregate.sbatch
#SBATCH --job-name=fd-agg
#SBATCH --account=bjej-dtai-gh
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=60G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source eval/env.sh
for v in ${VIEWS:-native face512}; do
  python -m eval.aggregate --detector "${DETECTOR:-decof}" --view "$v" ${EXTRA:-}
done
