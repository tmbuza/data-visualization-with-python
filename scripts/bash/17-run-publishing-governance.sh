#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export MPLCONFIGDIR="${repo_root}/.matplotlib-cache"
mkdir -p "${MPLCONFIGDIR}"

python_bin="${PYTHON:-python3}"
"${python_bin}" "${repo_root}/scripts/python/17_generate_governed_figures.py"
"${python_bin}" "${repo_root}/scripts/python/17_validate_figure_release.py"
