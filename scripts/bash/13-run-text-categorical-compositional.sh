#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/dvp-matplotlib"
mkdir -p "$MPLCONFIGDIR"

python_bin="python3"
if [[ -x ".venv/bin/python" ]]; then
  python_bin=".venv/bin/python"
fi

"$python_bin" scripts/python/13-text-categorical-compositional.py
echo "DVP 13 workflow completed."
