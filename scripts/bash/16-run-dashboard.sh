#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
export MPLCONFIGDIR="${REPO_ROOT}/.matplotlib-cache"
mkdir -p "${MPLCONFIGDIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

"${PYTHON_BIN}" "${REPO_ROOT}/scripts/python/16-build-dashboard.py" --root "${REPO_ROOT}" "$@"
