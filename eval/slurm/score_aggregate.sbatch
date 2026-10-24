#!/usr/bin/env bash
# One queue wait: score every rendered, unscored clip of the listed views (optionally only the
# ids in IDS_<view>), then aggregate each view that is complete (file-locked).
#   sbatch --export=ALL,DETECTOR=decof,BATCH=fake_b1,VIEWS="native face512",IDS_face512=<file> eval/slurm/score_aggregate.sbatch
# Sizing (measured): scoring runs ~27 clips/s; DataLoader memory ~ workers x prefetch x batch x
# 4.8 MB, doubled by pinning: 30 x 2 x 32 -> ~19 GB + ~6 GB base (prefetch 4 OOM-killed at 40 GB).
# ~7k clips ~5 min; aggregate a few min per view. Limit ~1.5x.
#SBATCH --job-name=fd-sa
#SBATCH --account=bjej-dtai-gh
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=40G
#SBATCH --time=00:25:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source eval/env.sh
for v in ${VIEWS}; do
  var="IDS_${v}"; ids="${!var:-}"
  python -m eval.run --detector "$DETECTOR" --view "$v" --batch "$BATCH" \
    ${ids:+--only-ids "$ids"} --batch-size 32 --workers 30 --prefetch 2
done
python -m eval.finalize aggregate-if-complete --detector "$DETECTOR" --views ${VIEWS} --compare
