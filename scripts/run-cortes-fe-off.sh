#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

FE_ENABLED="${1:-false}"

pixi run python src/process-pdf.py \
  'assets/Cortes-Gomez et al. - 2025 - Utility-Directed Conformal Prediction A Decision-Aware Framework for Actionable Uncertainty Quantif.pdf' \
  --out runs/slurm-cortes-fe-off \
  --formula-enrichment "$FE_ENABLED" \
  --ocr false
