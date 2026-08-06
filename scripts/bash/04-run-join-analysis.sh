#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python_bin="${PYTHON:-python3}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$repo_root/.matplotlib-cache}"

cd "$repo_root"
"$python_bin" scripts/python/04-join-analysis.py
