#!/usr/bin/env bash
# Start one headless ComfyUI server per visible GPU, ports BASE_PORT, BASE_PORT+1, ...
# Prints the --hosts string for run_batch.py and waits until every server answers.
#   eval "$(bash scripts/launch_comfy.sh)"   # exports FAIRDEEP_HOSTS
# Env: FAIRDEEP_COMFY_ROOT, VENV, BASE_PORT (8188), GPUS (default: all from nvidia-smi
# or CUDA_VISIBLE_DEVICES), LOG_DIR (default $COMFY/logs).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
COMFY="${FAIRDEEP_COMFY_ROOT:-$(dirname "$HERE")/ComfyUI}"
VENV="${VENV:-$(dirname "$HERE")/.venv}"
BASE_PORT="${BASE_PORT:-8188}"
LOG_DIR="${LOG_DIR:-$COMFY/logs}"
if [ -z "${GPUS:-}" ]; then
  if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then GPUS="$CUDA_VISIBLE_DEVICES"
  else GPUS="$(nvidia-smi --query-gpu=index --format=csv,noheader | paste -sd,)"; fi
fi
mkdir -p "$LOG_DIR"
PIDS="$LOG_DIR/comfy.pids"   # stop with: kill $(cat $PIDS)
: > "$PIDS"

hosts=()
i=0
for g in ${GPUS//,/ }; do
  port=$((BASE_PORT + i))
  CUDA_VISIBLE_DEVICES="$g" nohup "$VENV/bin/python" "$COMFY/main.py" \
    --listen 127.0.0.1 --port "$port" --disable-auto-launch \
    > "$LOG_DIR/comfy_gpu${g}_${port}.log" 2>&1 &
  echo $! >> "$PIDS"
  hosts+=("127.0.0.1:$port")
  i=$((i + 1))
done

for h in "${hosts[@]}"; do
  until curl -sf "http://$h/system_stats" >/dev/null; do sleep 5; done
  echo "ready: $h" >&2
done
echo "export FAIRDEEP_HOSTS=$(IFS=,; echo "${hosts[*]}") FAIRDEEP_PIDS=$PIDS"
