#!/bin/bash
#SBATCH --job-name=fairdeep-real
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=16
#SBATCH --time=12:00:00
#SBATCH --output=logs/filter_real_%j.out
#
# Conform already-fetched real segments to the synthetic spec, then label them.
#
# Only steps 3 and 4 of real/README.md run here. Fetching is deliberately NOT in
# this job: YouTube throttles and often blocks datacenter IP ranges, so
# fetch_celebvhq.py tends to fail en masse from a cluster even though it works
# from a laptop. Fetch elsewhere, stage RAW_ROOT here, then submit this.
#
#   RAW_ROOT=../celebvhq_raw OUT_ROOT=../fairdeep-bench/real sbatch slurm/filter_real.sbatch

set -euo pipefail

RAW_ROOT="${RAW_ROOT:-../celebvhq_raw}"
OUT_ROOT="${OUT_ROOT:-../fairdeep-bench/real}"
WEIGHTS="${WEIGHTS:-models/res34_fair_align_multi_7_20190809.pt}"
PER_CELL="${PER_CELL:-90}"
MAX_UPSCALE="${MAX_UPSCALE:-2.0}"
MIN_DUR="${MIN_DUR:-2.0}"          # shortest clean run kept; clips are not trimmed
PY="${PY:-../.venv/bin/python}"

# Bridges-2 / DeltaAI keep weights off the home quota; env.sh exports the paths.
if [ -f "${FAIRDEEP_ENV:-}" ]; then
    # shellcheck disable=SC1090
    source "$FAIRDEEP_ENV"
fi

mkdir -p logs "$OUT_ROOT"

echo "=== conform $RAW_ROOT -> $OUT_ROOT (min_dur=$MIN_DUR max_upscale=$MAX_UPSCALE)"
"$PY" real/filter_real.py \
    --videos "$RAW_ROOT" \
    --out-root "$OUT_ROOT" \
    --min-dur "$MIN_DUR" \
    --max-upscale "$MAX_UPSCALE" \
    --report manifests/qc_report_real.csv

echo "=== FairFace labels"
"$PY" real/label_strata.py --stage label \
    --clips "$OUT_ROOT" --weights "$WEIGHTS" --device cuda

echo "=== stratified selection (per-cell $PER_CELL)"
"$PY" real/label_strata.py --stage select \
    --clips "$OUT_ROOT" --per-cell "$PER_CELL" \
    --out manifests/strata_selection_real.csv \
    --coverage manifests/cell_coverage_real.csv

echo "=== done; read manifests/cell_coverage_real.csv before trusting the balance"
