#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${PYTHON_BIN:-python3}"

cd "$repo_root"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/dvp18-matplotlib"
mkdir -p "$MPLCONFIGDIR"
"$python_bin" scripts/python/18-end-to-end-visualization-case-study.py

echo "DVP 18 visualization workflow completed."
