#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/dvp03-matplotlib}"
python scripts/python/03-filtering-aggregation-and-grouping.py
