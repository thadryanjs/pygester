#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

FE_ENABLED="${1:-false}"

pixi run python src/process-pdf.py \
  'assets/Nikishin et al. - 2022 - Control-Oriented Model-Based Reinforcement Learning with Implicit Differentiation.pdf' \
  --out runs/slurm-nikishin-fe-off \
  --formula-enrichment "$FE_ENABLED" \
  --ocr false
