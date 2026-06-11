# Project Specification

This tool prepares a scientific paper (PDF) for AI-assisted analysis by producing a structured "context packet" and associated visual artifacts. It is an opinionated bundle producer that transforms a raw PDF into a set of machine-readable and human-verifiable artifacts.

## Core Philosophy
- **Faithfulness to Parser**: We trust the parser (Docling) to define the document structure. We do not demote, promote, or "fix" section headings.
- **Visual Ground Truth**: Every structured artifact (equation, figure, code block) is paired with a raster crop from the original PDF to allow instant visual verification.
- **No LLM in the Loop**: The pipeline is purely deterministic and requires no API keys. It prepares inputs *for* LLM workflows run elsewhere.
- **Reproducibility**: Every run records its provenance (input SHA, tool versions, CLI flags) in a manifest.

## Pipeline Stages

### parse
Extracts raw content and rasterizes pages.
- **Inputs**: PDF file.
- **Process**:
    - Invokes Docling to produce a structured JSON representation of the document.
    - On macOS (Darwin), forces CPU execution to avoid MPS float64 incompatibility.
    - Rasterizes all pages to PNGs at a specified DPI (default 200).
- **Outputs**:
    - `debug/original.pdf`: Copy of source.
    - `debug/parser/raw_output.json`: Docling's structured output.
    - `debug/parser/raw_output.md`: Docling's markdown export.
    - `pages/page_NNNN.png`: Full-page rasters.
    - `debug/run-manifest.json`: Detailed run provenance.

### clean
Processes the raw output into clean markdown and visual crops.
- **Inputs**: `raw_output.json`, `raw_output.md`, page PNGs.
- **Process**:
    - **Markdown Post-processing**: 
        - Normalizes ligatures, preserves math symbols, rejoins hyphenated words.
        - Drops page headers/footers.
        - Prepends YAML frontmatter.
    - **Visual Extraction**:
        - Walks the Docling AST to find equations, figures, and code blocks.
        - For each block, crops the corresponding page PNG using the provided bbox.
        - Saves crops to `visuals/` (e.g., `visuals/equations/equation_001.png`).
    - **Sidecar Generation**:
        - Writes `equations.json`, `figures.json`, `code.json`, `tables.json`, and `references.json`.
        - Each entry includes `id`, `page`, `bbox`, `content` (LaTeX/text), and `image_path`.
- **Outputs**:
    - `paper.md`: The cleaned, frontmatter-enhanced markdown.
    - `visuals/`: Directory containing cropped images and their corresponding JSON sidecars.
    - `tables/tables.json`: Extracted tables.
    - `references/references.json`: Extracted references.
    - `debug/intermediate/`: Intermediate text and provenance files.

### packet
Composes the final handoff bundle.
- **Inputs**: Artifacts from parse and clean stages.
- **Process**:
    - **Context Packet**: Aggregates all structured data into `context-packet.json`.
    - **Technical Summary**: Produces `technical-summary.md` containing the abstract and all equations grouped by section (using LaTeX if enrichment is on).
    - **Manifest**: Generates a human-readable `MANIFEST.md` explaining the run and deliverables.
    - **Quality Report**: Refreshes `quality-report.json` with final existence and count checks.
- **Outputs**:
    - `context-packet.json`: The primary structured handoff.
    - `technical-summary.md`: Math-focused summary for LLM pasting.
    - `MANIFEST.md`: Human-readable explainer.
    - `quality-report.json`: Final quality gates.

## Deliverables Layout
```
OUT_DIR/
├── MANIFEST.md
├── paper.md
├── technical-summary.md
├── context-packet.json
├── quality-report.json
├── pages/
│   └── page_NNNN.png
├── visuals/
│   ├── equations/
│   │   ├── equations.json
│   │   └── equation_NNN.png
│   ├── figures/
│   │   ├── figures.json
│   │   └── figure_NNN.png
│   └── code/
│       ├── code.json
│       └── code_NNN.png
├── tables/
│   └── tables.json
└── references/
    └── references.json
```

## CLI Interface
- **Positional**: `pdf_path`
- **Flags**:
    - `--out <dir>`: Output directory.
    - `--formula-enrichment <true|false>`: Use Docling's formula enrichment for LaTeX.
    - `--code-enrichment <true|false>`: Enable code block extraction and cropping.
    - `--ocr <true|false>`: Enable OCR for scanned PDFs.
    - `--max-pages <int>`: Limit processing to N pages.
    - `--dpi <int>`: Rasterization DPI (default 200).

## Quality Gates
Advisory bools in `quality-report.json`:
- `paper_md_exists`: `paper.md` exists and is non-empty.
- `has_references_section`: At least one reference was extracted.
- `raster_page_count_ok`: Number of page PNGs matches manifest page count.
- `technical_summary_exists`: `technical-summary.md` is non-empty.
- `technical_summary_has_equations`: Contains at least one equation block.

## Hard Constraints
1. **Pure Python**: No system CLI dependencies beyond Python and its packages.
2. **Source Truth**: Original PDF is preserved as the root artifact.
3. **No API Keys**: Pipeline is entirely local and deterministic.
4. **Provenances**: Every run is recorded via SHA and manifest for reproducibility.

## Future Work (Deferred)
- **Auto-OCR**: Detect if PDF is scanned and flip `--ocr` automatically.
- **Batch Mode**: Process multiple PDFs in one command.
- **Texify Fallback**: Use a specialized model to fix malformed LaTeX for specific equations.
- **Advanced Bibliography**: Full BibTeX/RIS parsing.
