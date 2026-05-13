#!/bin/bash
#SBATCH --job-name="digest-test-true"
#SBATCH --error="logs/digest-test-true.log"
#SBATCH --output="logs/digest-test-true.log"
#SBATCH --time=02-00:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL

# Test pipeline with formula enrichment (deep read - slow)
cd "$SLURM_SUBMIT_DIR"

echo "Starting Foffano test (formula-enrichment=true)..."
pixi run python scripts/process-pdf.py \
  'assets/Foffano et al. - 2023 - Conformal Off-Policy Evaluation in Markov Decision Processes.pdf' \
  --out runs/slurm-foffano-true \
  --formula-enrichment true \
  --code-enrichment false \
  --ocr false

echo "Formula enrichment test complete"
