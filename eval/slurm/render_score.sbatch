#!/usr/bin/env bash
# One queue wait per shard: render a view shard, score exactly that shard, and aggregate the
# view if this was the last missing piece (file-locked, so concurrent shards aggregate once).
#   sbatch --export=ALL,VIEW=face512,BATCH=fake_b1,SHARD=2,NSHARDS=4,DETECTOR=decof eval/slurm/render_score.sbatch
# Sizing from measured runs: face512 render shard 17 min, CPU-bound (~69 of 72 cores), 11.4 GB
# peak; scoring a shard ~5 min. Limit ~1.5x.
#SBATCH --job-name=fd-rs
#SBATCH --account=bjej-dtai-gh
#SBATCH --partition=ghx4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=72
#SBATCH --mem=24G
#SBATCH --time=00:35:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source eval/env.sh
IDS="logs/ids_${VIEW}_${BATCH}_s${SHARD}of${NSHARDS}_${SLURM_JOB_ID}.txt"
python -m eval.finalize ids --view "$VIEW" --batch "$BATCH" --shard "$SHARD" --nshards "$NSHARDS" > "$IDS"
python -m eval.preprocess --view "$VIEW" --batch "$BATCH" --shard "$SHARD" --nshards "$NSHARDS" --workers 36
python -m eval.run --detector "$DETECTOR" --view "$VIEW" --batch "$BATCH" --only-ids "$IDS" \
  --batch-size 32 --workers 64
python -m eval.finalize aggregate-if-complete --detector "$DETECTOR" --views "$VIEW" --compare
