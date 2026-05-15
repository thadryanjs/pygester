#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

FE_ENABLED="${1:-true}"

pixi run python src/process-pdf.py \
  'assets/Cortes-Gomez et al. - 2025 - Utility-Directed Conformal Prediction A Decision-Aware Framework for Actionable Uncertainty Quantif.pdf' \
  --out runs/slurm-cortes-true \
  --formula-enrichment "$FE_ENABLED" \
  --ocr false
