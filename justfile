set shell := ["bash", "-euo", "pipefail", "-c"]

# Create/update uv env from pyproject + lockfile
sync:
    uv sync --frozen

# Compile-check Python sources
check:
    uv run python -m py_compile src/*.py src/parsers/*.py

# Verify enrichment output in run directory (this will likley have been run on the ) server and need to be synced
qc-enrichment run_dir:
    bash scripts/qc-enrichment.sh {{run_dir}}

# Run Texify inference on equation crops
test-texify:
    uv run python tests/texify_test.py

# Pull runs + logs from server storage to local
local-pull-runs src='/mnt/Workspace/Pygester/runs/' dest='runs/' logsrc='/mnt/Workspace/Pygester/logs/' logdest='logs/':
    rsync -avz --delete "{{src}}" "{{dest}}"
    rsync -avz "{{logsrc}}" "{{logdest}}"

# Watch local files and rsync to remote work dir (requires watchexec)
watch:
    watchexec -r \
      rsync -avz --delete \
      --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
      --exclude='.egg-info' --exclude='_build' \
      --exclude='.git' --exclude='.opencode/node_modules/' \
      --include='*/' --include='*.py' --include='*.md' --include='*.toml' \
      --include='*.json' --include='*.ipynb' --include='*.sh' --exclude='*' \
      ./ /mnt/Workspace/Pygester

# Cleanup generated runs
clean:
    rm -rf testrun run-foffano run-cortes runs

# Test minimal pipeline: parse only, no enrichment (fast)
local-test-basic pdf='assets/Nikishin et al. - 2022 - Control-Oriented Model-Based Reinforcement Learning with Implicit Differentiation.pdf':
    uv run python src/process-pdf.py '{{pdf}}' \
      --out testrun/basic-test \
      --formula-enrichment false \
      --ocr false \
      --max-pages 5
