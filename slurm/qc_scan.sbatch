#!/usr/bin/env bash
# Technical QC scan on a compute node. scan.py is CPU-only, but this project's
# allocation is GPU-only, so the smallest GPU-shared job is the cheapest way to
# get uncontended cores: ~0.2 SU for 420 clips. Do not run it on a login node -
# those are shared and can sit at a load average far above their core count,
# where one clip takes 80s instead of 8s.
# The GPU is never used - it is only what this allocation can buy. Do not pin a
# GPU type: GPU-shared has 3 L40S nodes against 11+ V100 nodes, so an untyped
# request schedules far sooner at the same cost.
#   sbatch slurm/qc_scan.sbatch
#   TAG=wan22 ROOT=/path/to/synthetic WORKERS=16 sbatch slurm/qc_scan.sbatch
#SBATCH --job-name=fairdeep-qc
#SBATCH --account=cis260353p
#SBATCH --partition=GPU-shared
#SBATCH --gres=gpu:1
#SBATCH --time=00:40:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
source /ocean/projects/cis260353p/rahamed/fairdeep/env.sh
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
mkdir -p logs
"$VENV/bin/python" qc/scan.py --root "${ROOT:-$OUT_ROOT}" --out-dir manifests \
  --tag "${TAG:-hunyuan15}" --faces --workers "${WORKERS:-${SLURM_CPUS_ON_NODE:-8}}"
