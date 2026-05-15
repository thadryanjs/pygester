#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

FE_ENABLED="${1:-false}"

pixi run python src/process-pdf.py \
  'assets/Foffano et al. - 2023 - Conformal Off-Policy Evaluation in Markov Decision Processes.pdf' \
  --out runs/slurm-foffano-fe-off \
  --formula-enrichment "$FE_ENABLED" \
  --ocr false
