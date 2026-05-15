#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

FE_ENABLED="${1:-false}"

pixi run python src/process-pdf.py \
  'assets/Mishmast Nehi et al. - 2020 - Solving methods for interval linear programming problem a review and an improved method.pdf' \
  --out runs/slurm-mishmast-fe-off \
  --formula-enrichment "$FE_ENABLED" \
  --ocr false
