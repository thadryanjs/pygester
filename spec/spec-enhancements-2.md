# spec-enhancements-2.md

Add minimal pipeline logging using Python's `logging` stdlib. Goal: every run prints stage transitions to stdout in real time and persists them to `debug/run.log` so you can answer "is it hung or just slow" without `top`. No external dependencies, no JSON, no fancy formatting.

## Library

`logging` from the stdlib. Nothing else.

## Logger setup

In `scripts/common.py`, add a function called once at the start of each script:

```python
import logging
from pathlib import Path

def setup_logging(out_dir: Path) -> logging.Logger:
    """Configure root logger to write to stdout AND debug/run.log."""
    log_path = out_dir / "debug" / "run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()  # in case it's been configured before

    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    file_handler = logging.FileHandler(log_path, mode="a")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    return logging.getLogger("digest")
```

Called from each stage script:

```python
log = setup_logging(out_dir)
log.info("Stage 01 starting")
```

Append mode (`mode="a"`) means `process-pdf.py` running three stages in sequence accumulates everything in one log file. Each stage opens it, adds its lines, closes it.

## What gets logged

Stage boundaries plus a few useful intermediates. Not every line of work — just enough to know where we are.

**Stage 01 — Parse**

- `Stage 01 starting`
- `Config: formula_enrichment=<on|off>, code_enrichment=<on|off>, ocr=<on|off>, dpi=<N>`
- `Loading Docling`
- `Loading complete (Xs)`
- `Parsing <input.pdf>`
- `Parse complete (Xs)`
- `Rasterizing <N> pages at <DPI> DPI`
- `Rasterization complete (Xs) — wrote <N> PNGs`
- `Stage 01 done (Xs total)`

**Stage 02 — Clean**

- `Stage 02 starting`
- `Walking Docling AST`
- `Wrote <N> equations, <N> figures, <N> tables, <N> references`
- `Wrote paper.md (<N> KB)`
- `Stage 02 done (Xs total)`

**Stage 03 — Packet**

- `Stage 03 starting`
- `Wrote context-packet.json (<N> KB)`
- `Wrote technical-summary.md (<N> KB)`
- `Wrote quality-report.json`
- `Wrote MANIFEST.md`
- `Stage 03 done (Xs total)`

**process-pdf.py wrapper**

- `Total elapsed: Xs` at the very end

## Timing pattern

```python
import time

t0 = time.monotonic()
# ... do work ...
log.info(f"Parse complete ({time.monotonic() - t0:.1f}s)")
```

`time.monotonic()` because it's not affected by clock adjustments mid-run. Format elapsed times to one decimal.

## Levels

Everything in the list above is `INFO`. Use `WARNING` only for genuinely unexpected things (a stage finished but produced zero artifacts, a quality gate flipped). Use `ERROR` only when something failed in a way the user needs to see. Don't reach for `DEBUG` unless someone actually wants verbose output behind a future `--verbose` flag — for now, INFO is enough.

## What NOT to log

- Per-equation/per-figure progress (would be useful but requires hooking into Docling internals; out of scope for "small but tidy")
- The contents of artifacts (use the artifacts themselves for that)
- Stack traces from non-fatal warnings (let them go to stderr)
- Anything that prints multiple times per second (would clutter the log file)

## Suppressing noisy library logs

Docling and transformers will print their own logging via `logging` too. Without intervention, those messages will show up in your log file at WARNING level and clutter things. Suppress them in `setup_logging`:

```python
for noisy in ("docling", "transformers", "huggingface_hub", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.ERROR)
```

This silences their INFO/WARNING messages but lets real errors through. The transformers "tied weights" warning you've been seeing repeatedly will stop appearing in your run log. (It still goes to stderr from transformers' own print calls — that's a separate issue not worth chasing.)

## Output destination

- **Stdout**: line-buffered so it appears in real time when running interactively or via `pixi run`. `logging.StreamHandler()` does this by default.
- **`debug/run.log`**: persisted in the run's debug directory. Survives the run, accessible for post-hoc inspection.
- **Slurm**: stdout gets captured to the job's `.out` file automatically. Both destinations work without changes.

The log file is unbounded — long runs produce longer logs. With this minimal scope, even an hour-long Docling run produces well under 100 lines. No rotation needed.

## Verification

After the change, a run should look like this in the terminal:

```
$ pixi run test-foffano-enrichment-on
[14:32:01] Stage 01 starting
[14:32:01] Config: formula_enrichment=on, code_enrichment=off, ocr=off, dpi=200
[14:32:01] Loading Docling
[14:32:08] Loading complete (7.2s)
[14:32:08] Parsing assets/Foffano et al. - 2023 - Conformal ... .pdf
[14:58:33] Parse complete (1585.4s)
[14:58:33] Rasterizing 8 pages at 200 DPI
[14:58:35] Rasterization complete (1.8s) — wrote 8 PNGs
[14:58:35] Stage 01 done (1593.4s total)
[14:58:35] Stage 02 starting
[14:58:35] Walking Docling AST
[14:58:36] Wrote 30 equations, 4 figures, 0 tables, 33 references
[14:58:36] Wrote paper.md (15.3 KB)
[14:58:36] Stage 02 done (0.9s total)
[14:58:36] Stage 03 starting
[14:58:36] Wrote context-packet.json (2.1 KB)
[14:58:36] Wrote technical-summary.md (4.7 KB)
[14:58:36] Wrote quality-report.json
[14:58:36] Wrote MANIFEST.md
[14:58:37] Stage 03 done (0.4s total)
[14:58:37] Total elapsed: 1594.7s
```

And `runs/foffano-fe-on/debug/run.log` contains the same lines.

## What this fixes

The "is it hung?" anxiety. When you see `[14:32:08] Parsing assets/Foffano ... .pdf` and then nothing for 20 minutes, you know Docling is doing the slow thing. When you see no new lines after a stage transition and `top` shows 0% CPU, you know it's actually stuck. The log is the diagnostic.

It also makes Slurm jobs much more debuggable — the `.out` file from a job has the same content as `debug/run.log`, so you can tail it from anywhere without rsync.

## What it does NOT fix

This is logging, not progress reporting. You still won't know which equation Docling is currently processing during the 20-minute parse step — that would require hooking into Docling's internal callbacks and is out of scope. If you want it later, it's a separate enhancement (Docling exposes some progress events you can subscribe to; would be its own design discussion).
