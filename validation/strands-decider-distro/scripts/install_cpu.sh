#!/usr/bin/env bash
# Install strands-decider + CPU torch into $VENV_DIR (default: $HOME/venv).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/versions.env"

VENV_DIR="${VENV_DIR:-$HOME/venv}"
python3 -m venv "${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install "strands-decider==${STRANDS_DECIDER_VERSION}"
python -c "import strands_decider, torch; print('strands-decider', strands_decider.__version__, 'torch', torch.__version__)"
