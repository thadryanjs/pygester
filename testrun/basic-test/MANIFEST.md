# Run manifest

This directory contains the output of `digest-technical-paper` processing
`assets/Nikishin et al. - 2022 - Control-Oriented Model-Based Reinforcement Learning with Implicit Differentiation.pdf`.

Tool version: `0.1.0` · Run at: `2026-06-11T15:54:39.698016+00:00` · Flags: `--formula-enrichment false --code-enrichment off --ocr false`

## What's in here

### Deliverables (the things you probably want)

- **`paper.md`** — the paper as cleaned markdown. Section structure preserved.
  Math is Unicode (formula enrichment off).
- **`technical-summary.md`** — abstract + every equation, grouped by section.
  For math-focused chats: equation translation, derivation checks, code
  generation. Smaller than `paper.md`, faster to paste.
- **`context-packet.json`** — structured metadata: sections with page ranges,
  figures, tables, equations, references. The thing to paste alongside `paper.md`
  when an LLM needs to know what's on each page.
- **`pages/page_NNNN.png`** — one rasterized image per page (5 total).
  Use these when you want to show an LLM what a figure or equation actually looks like.
- **`visuals/`** — per-block crops: `equations/`, `figures/`, `code/`. Each has
  a JSON manifest plus PNG crops. Visual ground truth for verification.
- **`tables/`** — extracted tables as JSON (if any found).
- **`references/`** — extracted references as JSON (if any found).
- **`quality-report.json`** — quick summary of what's populated and what failed.
  Glance at this if `paper.md` looks weird.

### Debug

Everything under `debug/` is plumbing — intermediate artifacts that exist so a
future debugger can trace what each stage did. You can ignore these unless
something's wrong.

- `debug/original.pdf` — the input, copied here so the run is self-contained.
- `debug/run-manifest.json` — full config: every flag, parser version, hashes,
  per-stage timing.
- `debug/parser/raw_output.{json,md}` — what Docling produced before our post-
  processing. Compare against `paper.md` to see what the clean stage changed.
- `paper-text.md` — canonical text without markdown formatting.
- `debug/sections.json` — section tree (already in context-packet).
- `debug/markdown/` — intermediate snapshots from clean-stage post-processing.
- `debug/{figures,tables,equations,references}/` — structured artifacts
  that get rolled into `context-packet.json`.

## What was done to your paper

- Docling version: `2.96.0`
- Formula enrichment: `false` — math came through as Unicode (formula enrichment off)
- Code enrichment: `off` — code blocks raw text
- OCR: `false` — skipped; PDF had usable text layer
- Pages processed: 5
- Sections detected: 18
- Figures detected: 7
- Tables detected: 1
- Equations detected: 19
- Equations in technical summary: 19

## Quality gates

- **paper_md_exists**: ✓
- **has_references_section**: ✗
- **raster_page_count_ok**: ✓
- **technical_summary_exists**: ✓
- **technical_summary_has_equations**: ✓

## Reproducing this run

```bash
python src/parse.py "assets/Nikishin et al. - 2022 - Control-Oriented Model-Based Reinforcement Learning with Implicit Differentiation.pdf" --out <OUT_DIR> --formula-enrichment false --code-enrichment false --ocr false
python src/clean.py --out <OUT_DIR>
python src/packet.py --out <OUT_DIR>
```
