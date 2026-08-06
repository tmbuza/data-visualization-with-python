#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

export MPLCONFIGDIR="${TMPDIR:-/tmp}/dvp-14-matplotlib"
mkdir -p "$MPLCONFIGDIR"

python scripts/python/14_accessible_design.py
