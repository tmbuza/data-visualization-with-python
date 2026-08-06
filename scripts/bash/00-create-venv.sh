#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python3.12}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} was not found. Install Python 3.12 or set PYTHON_BIN." >&2
  exit 1
fi

if [[ -d .venv ]]; then
  echo "Error: .venv already exists. Remove or rename it before requesting a fresh environment." >&2
  exit 1
fi

"${PYTHON_BIN}" -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ipykernel install --user \
  --name visualization-with-python \
  --display-name "Python (Visualization with Python)"

echo
echo "Environment created successfully."
echo "Activate it with: source .venv/bin/activate"
