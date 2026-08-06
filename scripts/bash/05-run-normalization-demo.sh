#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

python scripts/python/05-normalization-demo.py \
  --schema scripts/sql/05-normalized-order-schema.sql \
  --summary results/05-normalization-summary.csv \
  --figure results/figures/05-normalization-comparison.png

