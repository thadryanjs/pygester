# digest-technical-paper — Spec

## What this is

A Docling wrapper. Takes a scientific PDF and produces a clean bundle of `(paper.md, page PNGs, context-packet.json)` for AI workflows. Augments Docling's defaults with page rasterization and a curated metadata sidecar, but does not reinvent any of the parsing.

Built by an academic for personal use. Not a product.

## The deal

```
PDF  ──Docling──>  paper.md   (markdown, optionally enriched with LaTeX/code)
PDF  ──PyMuPDF──>  pages/*.png  (one image per page)
both ──our code──>  context-packet.json  (sections, figures, tables, equations, references, provenance)
```

That's the whole tool.

## What "enrichment" means

Docling does layout detection by default — it finds blocks and labels them (text, picture, formula, table, code). Enrichment is optional extra model passes that fill in the *content* of those blocks beyond layout:

- **Formula enrichment**: for blocks tagged `formula`, run a vision model that outputs LaTeX. Without this, equations come through as flattened Unicode soup.
- **Code enrichment**: for blocks tagged `code` (pseudocode, snippets), run a model that extracts clean text and tags the programming language.
- **OCR**: for PDFs with no text layer, run an OCR engine. Not needed for modern native-text papers.

Each enrichment is a separate model load and inference pass. They're slow. They're off by default.

## Defaults and toggles

Defaults favor **fast triage**: no enrichment, no OCR. A run takes seconds, math is degraded to Unicode, code blocks may be noisy. Good enough for "give me 5 papers as markdown so I can skim them with an LLM."

For a "deep read" workflow, opt in:

```bash
python scripts/03-packet.py paper.pdf --out runs/foo \
  --formula-enrichment on \
  --code-enrichment on
```

A deep-read run takes minutes (multiple model loads + per-block inference) but produces LaTeX math and clean code blocks in `paper.md`.

All toggles are recorded in the run manifest so any output is reproducible from its config.

## Scripts (and order)

Three numbered scripts. Each is runnable standalone for debugging; `process-pdf.py` runs them all in order.

```
01-parse.py     # PDF → Docling raw outputs + page PNGs
02-clean.py     # Docling outputs → cleaned markdown + structured sidecars
03-packet.py    # all artifacts → context-packet.json
process-pdf.py  # runs 01 → 02 → 03 in order
```

## CLI

```bash
python scripts/process-pdf.py INPUT.pdf --out OUT_DIR [flags]
```

Flags:

| Flag | Default | Effect |
|---|---|---|
| `--formula-enrichment {on,off}` | off | Docling formula → LaTeX. Costs minutes per paper. |
| `--code-enrichment {on,off}` | off | Docling code blocks → clean text + language tags. Costs minutes per paper. |
| `--ocr {on,off}` | off | Docling OCR. Native-text PDFs don't need it. |
| `--max-pages N` | none | Process only first N pages (testing). |
| `--dpi N` | 200 | Page raster DPI. |
| `--cache` | off | Skip re-parse if input SHA matches existing manifest. |

Exit codes:

- `0` — success
- `1` — input PDF missing or unreadable
- `2` — uncaught exception (stderr has the traceback)

## Outputs

Deliverables are at the top of `OUT_DIR/`. Everything else is debug plumbing, tucked under `debug/`.

```
OUT_DIR/
├── MANIFEST.md               # auto-generated; explains every file in this directory
├── paper.md                  # cleaned markdown, post-processed Docling
├── context-packet.json       # structured sidecar
├── quality-report.json       # which gates passed, what's missing
├── pages/                    # one image per page
│   └── page_0001.png …
└── debug/
    ├── original.pdf          # verbatim copy of input
    ├── run-manifest.json     # config, flags, hashes, timestamps
    ├── parser/
    │   ├── raw_output.json   # Docling DoclingDocument as JSON (large)
    │   └── raw_output.md     # Docling markdown export, pre-cleanup
    ├── text/
    │   ├── plaintext.txt     # cleaned canonical text
    │   ├── sections.json     # section tree (already in context-packet)
    │   └── provenance.json   # char-offset → page/bbox map
    ├── markdown/             # intermediate snapshots from Stage 02 post-processing
    │   └── 01-with-frontmatter.md …
    ├── figures/figures.json
    ├── tables/tables.json
    ├── equations/equations.json
    └── references/references.json
```

Deliverables (the top of `OUT_DIR/`) use kebab-case. Debug files keep snake_case (Docling convention).

### MANIFEST.md

Auto-generated at the end of every run. Plain English, written so a future-you or a collaborator opening the directory understands what each file is for without reading the spec.

Template:

```markdown
# Run manifest

This directory contains the output of `digest-technical-paper` processing
`<source filename>`.

Tool version: `<version>` · Run at: `<ISO timestamp>` · Flags: `<flag summary>`

## What's in here

### Deliverables (the things you probably want)

- **`paper.md`** — the paper as cleaned markdown. Section structure preserved.
  Math is <Unicode soup | LaTeX> depending on whether formula enrichment was on.
- **`context-packet.json`** — structured metadata: sections with page ranges,
  figures, tables, equations, references. The thing to paste alongside `paper.md`
  when an LLM needs to know what's on each page.
- **`pages/page_NNNN.png`** — one rasterized image per page (<N> total).
  Use these when you want to show an LLM what a figure or equation actually looks like.
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
  processing. Compare against `paper.md` to see what Stage 02 changed.
- `debug/text/plaintext.txt` — canonical text without markdown formatting.
  Redundant with `paper.md` for most uses.
- `debug/markdown/` — intermediate snapshots from the markdown post-processing
  chain. `01-with-frontmatter.md` is what `paper.md` looks like after only
  the first post-processing step, and so on.
- `debug/{figures,tables,equations,references}/*.json` — structured artifacts
  that get rolled into `context-packet.json`. Look here if the packet looks
  incomplete.

## What was done to your paper

- Docling version: `<X.Y.Z>`
- Formula enrichment: `<on|off>` — <"math came through as LaTeX" | "math came through as flattened Unicode">
- Code enrichment: `<on|off>` — <"code blocks cleaned" | "code blocks as raw text">
- OCR: `<on|off>` — <"OCR ran" | "OCR skipped; PDF had a usable text layer">
- Pages processed: `<N>` of `<M>`<br>
- Sections detected: `<N>`
- Figures detected: `<N>`
- Tables detected: `<N>`
- Equations detected: `<N>` <(only counts the ones formula enrichment processed if it was on)>

## Quality gates

<list of gates with ✓/✗ and short notes; mirror of quality-report.json>

## Reproducing this run

```bash
python scripts/process-pdf.py "<source filename>" --out <OUT_DIR> <flags>
```
```

The template is interpolated at write time. Conditional bits in `<angle brackets>` are filled in based on what actually happened.

`MANIFEST.md` is informational. Nothing in the pipeline reads it. It exists for the human who opens the folder a month later wondering what they were looking at.

## Stages

### Stage 01 — Parse

Run Docling with the configured toggles. Rasterize page PNGs via PyMuPDF.

Writes `debug/parser/`, `pages/`, initial `debug/run-manifest.json`.

### Stage 02 — Clean

Translate Docling's output into the internal artifact schema and produce `paper.md`.

Cleanup steps applied to canonical text and markdown:

- Normalize ligatures (`ﬁ→fi`, `ﬂ→fl`, etc.)
- Preserve em-dashes and math symbols verbatim
- Rejoin words split by line-end hyphens (when the joined form is a real word)
- Drop `page_header` and `page_footer` blocks (IEEE running headers, page numbers)
- Preserve LaTeX from formula enrichment verbatim

`paper.md` is produced by post-processing `debug/parser/raw_output.md` (Docling's markdown export). We do not rebuild from scratch — Docling's structure is faithful to the paper and we trust it. The post-processing steps are:

1. Prepend YAML frontmatter (source SHA, parser version, tool version, run timestamp, flags used)
2. Save the intermediate result to `debug/markdown/01-with-frontmatter.md`
3. Apply any future post-processing steps as numbered intermediates
4. Copy the final result to `paper.md`

If only step 1 fires, `01-with-frontmatter.md` and `paper.md` are identical (modulo path). That's fine. The numbered intermediates exist so a future debugger can see what each step did.

We do **not** demote, promote, classify, or "fix" Docling's section headings. If Docling calls `Algorithm 1` a section, it stays a section. If Docling tags the paper title as `section_header`, it stays an H1 in the markdown. The tool is faithful to Docling's choices.

Stage 02 also produces the structured sidecars: `sections.json`, `provenance.json`, `figures.json`, `tables.json`, `equations.json`, `references.json`. Each is best-effort based on what Docling provides; empty lists are valid outputs when Docling found nothing.

### Stage 03 — Packet

Compose `context-packet.json` from the debug artifacts. The packet is the structured handoff: title, sections with char-offset ranges, figures with captions and image paths, tables with CSV paths, equations with LaTeX and image paths, references, paper provenance, and an evidence index pointing at page PNGs.

Also writes `quality-report.json` (which artifacts are populated, which are empty, any warnings from Stages 01–02) and `MANIFEST.md` (auto-generated human-readable explainer; see Outputs section).

## Hard constraints

1. Pure Python via pip. No system CLI dependencies.
2. Original PDF preserved as source-of-truth artifact.
3. Pipeline runnable without LLM (no API keys required, ever).
4. Reproducibility through provenance, not bit-equality. Manifest records input SHA, parser version, parser config, all CLI flags, DPI, tool version, timestamp.

## Quality gates

Written to `quality-report.json`. Each is a bool plus a short note. None block the pipeline by default; they're advisory.

- `canonical_non_empty` — `debug/text/plaintext.txt` has content
- `has_references_section` — at least one section heading matches `^REFERENCES$|^BIBLIOGRAPHY$` (case-insensitive)
- `raster_page_count_ok` — number of page PNGs matches Docling's page count
- `paper_md_exists` — `paper.md` is non-empty
- `context_packet_valid` — `context-packet.json` parses as valid JSON with required keys

No `has_abstract` gate (Docling doesn't tag abstracts; we don't try to synthesize one). No `section_hierarchy_consistent` gate (we trust Docling's hierarchy). No `false_positive_demoted` anomalies (we don't demote anything).

## Dependencies

```
docling>=2.91.0
PyMuPDF>=1.24.0
pydantic>=2.8.0
orjson>=3.10.0
```

## Caching

`--cache` checks `debug/run-manifest.json` for matching input SHA *and* matching flag set. If both match, skip Stages 01–02 and rebuild Stage 03 only. Different flags = different cache key (a run with `--formula-enrichment on` does not satisfy a request for `--formula-enrichment off`).

## What this tool isn't

- Not an LLM caller. No API keys, no summary generation, no translation. The point is to *prepare* inputs for AI workflows you run elsewhere.
- Not a parser. Docling does the parsing. We package.
- Not a research project. No grand evaluation plan, no claim that this beats some baseline. It's an opinionated bundle producer.
- Not a stable product. Experimental, behaviors and outputs may change.

## Future work

Items deferred:

- **OCR auto-detection.** Currently `--ocr off` is the default; users with a scanned PDF flip it on knowingly. Auto-detect (cheap PyMuPDF text-layer check, override to on when chars/page < 100) is straightforward to add but not needed yet.
- **Picture description / classification.** Docling supports these enrichments too. Skipped because we already produce page PNGs, which is a more useful artifact than auto-generated captions.
- **Second parser backend.** If Docling regresses or something better arrives, the parser invocation in `01-parse.py` is localized and can be swapped. No Protocol abstraction needed at this scale.
- **Bibliography parsing.** Currently `raw` + parsed-by-Docling-if-possible. A proper BibTeX/RIS parser is downstream of this tool.
- **Batch mode.** `process-pdf.py paper1.pdf paper2.pdf paper3.pdf` for triaging a stack at once. Sensible add when the dev loop demands it.
