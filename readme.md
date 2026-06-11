# PyGester

A prototype. We're AI-skeptical academic data scientists and engineers who keep ending up using LLMs anyway, so we want to feed them well-prepared inputs instead of raw PDFs and hope.

This tool does **not** call an LLM. It produces a clean artifact bundle you hand to whichever AI you're already using — Claude, ChatGPT, a local model, a coworker.

> ⚠️ **Experimental.** We're actively messing with this. Behavior, output formats, and CLI flags will change without warning. Don't build anything on top of it that you'd be sad to rewrite.

## What it does

PDF in. Out comes:

- `paper.md` — cleaned markdown of the paper. Section structure preserved. Math kept as LaTeX. Ligatures and hyphenation normalized.
- `context-packet.json` — structured metadata: sections with page ranges, figures with captions, tables, equations, references. The thing you paste alongside the markdown when an LLM needs to know "what's on page 4."
- `pages/page_NNNN.png` — one rasterized page per page. Use them as evidence when discussing math, figures, or anything where the 2D layout matters.
- `quality-report.json` — what passed, what failed, what's suspicious. Read this before trusting the rest.

That's the whole tool.

## Quickstart

```bash
git clone <repo>
cd pygester
uv sync

uv run python src/process-pdf.py path/to/paper.pdf --out run/
```

Outputs land directly in `--out` directory. Intermediate artifacts in `debug/`. Both gitignored.

Task runner uses `just` (see `justfile`). Example: `just check`, `just qc runs/slurm-foffano-fe-on`.

Useful flags:

- `--max-pages N` — limit for testing on long papers
- `--dpi N` — page raster resolution (default 200)

No API keys. No network calls beyond Docling's model downloads on first install.

## What you do with the output

Whatever you want. A few patterns we use:

- **Paste `paper.md` into a chat and ask questions.** Better than pasting the PDF because the markdown is already cleaned. Way better than nothing.
- **Attach `paper.md` + `context-packet.json` together.** The packet tells the LLM what's on each page, so when you ask "explain Algorithm 1," the model can find it.
- **Attach individual page PNGs for math-heavy questions.** "Translate equation (11) to NumPy" works much better when you also attach `page_0005.png` showing the equation in its rendered 2D form.
- **Keep the bundle and reuse it.** Re-parsing a PDF every time you start a new chat is wasteful. The artifact bundle is small and stable.

## What it's built on

- **Docling** for PDF parsing. Layout, tables, math via formula enrichment, OCR when needed. It's already good. The point of this tool is to wrap it well, not replace it.
- **PyMuPDF** for page rasterization and a cheap pre-check on whether the PDF has a text layer (if not, we tell Docling to OCR).

The parser sits behind a thin Protocol so swapping Docling for something else later is one file. We don't expect to.

## Why bother

You could paste the PDF directly into an LLM and sometimes that works. The reasons we built this anyway:

1. Docling's markdown is consistently better than what an LLM extracts from a raw PDF, especially for math, tables, and multi-column layouts. Why pay tokens to parse the same PDF every chat?
2. Page-level provenance lets you and the LLM actually agree on what's where. `(p. 4)` means something specific.
3. The same artifact bundle feeds many chats cheaply. Parse once, reuse forever.
4. The cleaned markdown is useful on its own — not all LLM workflows are conversational.

We do not know if this consistently produces better AI-assisted research than pasting PDFs raw. That's the experiment.

## Known caveats

- **Section hierarchy.** Docling labels every heading `level: 1`, mislabels the paper title as a section header, and treats `Algorithm N` blocks as sections. No automatic correction is applied.
- **Abstracts aren't labeled.** Docling doesn't tag abstracts; no synthesis is attempted.
- **Scanned PDFs.** No auto-OCR. If your PDF has no text layer, you must pass `--ocr true` manually.
- **Quality gates report warnings, not failures, by default.** We've been burned by gates that claim everything's fine when it isn't. Treat them as hints.
- **No per-claim confidence scores.** Docling exposes some per-block confidence, but inconsistently. Don't expect calibrated uncertainty.

## Pipeline (for contributors)

```
PDF → parse → clean → packet
         ↘ PyMuPDF rasterize pages
```

Stages run in order:

1. **`src/parse.py`** — Docling extracts the PDF; PyMuPDF rasterizes pages. Writes raw Docling output + page PNGs.
2. **`src/clean.py`** — normalize markdown (ligatures, hyphenation), extract figures/tables/equations/references with crops + sidecar JSON.
3. **`src/packet.py`** — compose `context-packet.json`, `technical-summary.md`, `MANIFEST.md`.

`src/process-pdf.py` orchestrates by importing and calling each stage function. Each stage is also runnable standalone via its own CLI for debugging.

The interesting code is in `src/clean.py` and `src/packet.py` — that's where parser quirks get fixed. Docling does the heavy lifting; we clean up after it.

Detailed schemas, contracts, and stage-by-stage behavior live in [`spec/spec.md`](spec/spec.md). This README is the user-facing overview; the spec is what you read if you're building or modifying the tool.

## Future work

- **Texify sidecar.** Run Texify on equation crops when Docling formula enrichment fails.
- **Better math extraction.** Dedicated math model for complex formulas.
- **Equation numbering.** Extract/normalize equation numbers from Docling output.
