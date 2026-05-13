#!/bin/bash
#SBATCH --job-name="digest-test-false"
#SBATCH --error="logs/digest-test-false.log"
#SBATCH --output="logs/digest-test-false.log"
#SBATCH --time=00-01:00:00
#SBATCH --mem=2G
#SBATCH --mail-type=BEGIN,END,FAIL

# Test pipeline without enrichment (fast triage)
cd "$SLURM_SUBMIT_DIR"

echo "Starting Foffano test (enrichment=false)..."
pixi run python scripts/process-pdf.py \
  'assets/Foffano et al. - 2023 - Conformal Off-Policy Evaluation in Markov Decision Processes.pdf' \
  --out runs/slurm-foffano-false \
  --formula-enrichment false \
  --code-enrichment false \
  --ocr false

echo "Starting Cortes test (enrichment=false)..."
pixi run python scripts/process-pdf.py \
  'assets/Cortes-Gomez et al. - 2025 - Utility-Directed Conformal Prediction A Decision-Aware Framework for Actionable Uncertainty Quantif.pdf' \
  --out runs/slurm-cortes-false \
  --formula-enrichment false \
  --code-enrichment false \
  --ocr false

echo "All tests complete"
