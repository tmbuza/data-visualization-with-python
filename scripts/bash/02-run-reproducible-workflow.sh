#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -x "$project_root/.venv/bin/python" ]]; then
  python_bin="$project_root/.venv/bin/python"
else
  python_bin="python3"
fi

cd "$project_root"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/dvp-02-matplotlib"
mkdir -p "$MPLCONFIGDIR"
"$python_bin" scripts/python/02-reproducible-visualization-workflow.py
