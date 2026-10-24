#!/usr/bin/env bash
# One-time install on a new cluster: ComfyUI (pinned), custom nodes, Python env, weights.
#   bash setup.sh                 # LTX 2.3 only (~67 GiB of weights)
#   MODELS=all bash setup.sh      # + Wan 2.2 and HunyuanVideo 1.5 (~200 GiB)
# Env overrides: DFBENCH_COMFY_ROOT (default ../ComfyUI), VENV (default ../.venv),
#                TORCH_INDEX (default cu128 wheels), HF_HUB_CACHE.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
COMFY="${DFBENCH_COMFY_ROOT:-$(dirname "$HERE")/ComfyUI}"
VENV="${VENV:-$(dirname "$HERE")/.venv}"
MODELS="${MODELS:-ltx23}"
TORCH_INDEX="${TORCH_INDEX:-https://download.pytorch.org/whl/cu128}"

# Versions the 2,016-clip LTX run was produced with
COMFY_COMMIT=7972b5ba7f1597f68261be33c912f5e5dba8b9c0
VHS_COMMIT=4ee72c065db22c9d96c2427954dc69e7b908444b

if [ ! -d "$COMFY/.git" ]; then
  git clone https://github.com/Comfy-Org/ComfyUI.git "$COMFY"
fi
git -C "$COMFY" fetch --quiet origin && git -C "$COMFY" checkout --quiet "$COMFY_COMMIT"

VHS="$COMFY/custom_nodes/ComfyUI-VideoHelperSuite"
if [ ! -d "$VHS/.git" ]; then
  git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "$VHS"
fi
git -C "$VHS" fetch --quiet origin && git -C "$VHS" checkout --quiet "$VHS_COMMIT"

if command -v uv >/dev/null; then
  [ -d "$VENV" ] || uv venv --python 3.12 "$VENV"
  PIP="uv pip install --python $VENV/bin/python"
else
  [ -d "$VENV" ] || python3.12 -m venv "$VENV"
  PIP="$VENV/bin/pip install"
fi
$PIP torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0 --index-url "$TORCH_INDEX"
$PIP -r "$COMFY/requirements.txt" -r "$VHS/requirements.txt" -r "$HERE/requirements.txt"

"$VENV/bin/python" "$HERE/scripts/download_models.py" --comfy-root "$COMFY" --models "$MODELS"
echo "setup done: ComfyUI=$COMFY venv=$VENV models=$MODELS"
