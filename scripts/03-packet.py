"""Stage 03: Compose context-packet.json, MANIFEST.md, and final deliverables."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from common import read_json, write_json, setup_logging, ensure_dir

SKILL_VERSION = "0.1.0"


def build_context_packet(out_dir: Path) -> None:
    """Build context packet from artifacts."""
    debug = out_dir / "debug"
    manifest = read_json(debug / "run-manifest.json")
    quality = read_json(out_dir / "quality-report.json")

    # Load sidecars (nested per spec, only if directories exist)
    sections = read_json(debug / "text" / "sections.json") if (debug / "text" / "sections.json").exists() else []

    figures = []
    if (debug / "figures" / "figures.json").exists():
        figures = read_json(debug / "figures" / "figures.json")

    tables = []
    if (debug / "tables" / "tables.json").exists():
        tables = read_json(debug / "tables" / "tables.json")

    equations = []
    if (debug / "equations" / "equations.json").exists():
        equations = read_json(debug / "equations" / "equations.json")

    references = []
    if (debug / "references" / "references.json").exists():
        references = read_json(debug / "references" / "references.json")

    # Build packet
    packet = {
        "schema_version": "1",
        "paper_profile": {
            "title": "Unknown",
            "page_count": manifest.get("page_count", 0),
            "input_pdf_sha256": manifest.get("input_pdf_sha256", ""),
            "parser": manifest.get("parser", {}),
            "tool_version": SKILL_VERSION,
        },
        "sections": sections,
        "figures": figures,
        "tables": tables,
        "equations": equations,
        "references": references,
        "quality": {
            "status": quality.get("status", "ok"),
            "gates": quality.get("gates", {}),
        },
        "evidence_index": {
            "original_pdf": "debug/original.pdf",
            "pages_dir": "pages/",
            "page_paths": [f"pages/page_{i+1:04d}.png" for i in range(manifest.get("page_count", 0))],
        },
    }

    write_json(out_dir / "context-packet.json", packet)


def write_manifest_md(out_dir: Path) -> None:
    """Write human-readable MANIFEST.md."""
    debug = out_dir / "debug"
    manifest = read_json(debug / "run-manifest.json")
    quality = read_json(out_dir / "quality-report.json")

    flags = manifest.get("flags", {})
    parser = manifest.get("parser", {})
    config = parser.get("config", {})

    math_status = "LaTeX" if config.get("do_formula_enrichment") else "Unicode soup"
    code_status = "cleaned" if config.get("do_code_enrichment") else "raw text"
    ocr_status = "ran" if config.get("do_ocr") else "skipped; PDF had usable text layer"

    gates = quality.get("gates", {})
    gate_lines = [f"- **{k}**: {'✓' if v else '✗'}" for k, v in gates.items()]

    md = f"""# Run manifest

This directory contains the output of `digest-technical-paper` processing
`{manifest.get("input_pdf", "")}`.

Tool version: `{SKILL_VERSION}` · Run at: `{manifest.get("timestamp_utc", "")}` · Flags: `--formula-enrichment {flags.get("formula_enrichment", "off")} --code-enrichment {flags.get("code_enrichment", "off")} --ocr {flags.get("ocr", "off")}`

## What's in here

### Deliverables (the things you probably want)

- **`paper.md`** — the paper as cleaned markdown. Section structure preserved.
  Math is {math_status} depending on whether formula enrichment was on.
- **`context-packet.json`** — structured metadata: sections with page ranges,
  figures, tables, equations, references. The thing to paste alongside `paper.md`
  when an LLM needs to know what's on each page.
- **`pages/page_NNNN.png`** — one rasterized image per page ({manifest.get("page_count", 0)} total).
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
- `debug/parser/raw_output.{{json,md}}` — what Docling produced before our post-
  processing. Compare against `paper.md` to see what Stage 02 changed.
- `debug/text/plaintext.txt` — canonical text without markdown formatting.
- `debug/text/sections.json` — section tree (already in context-packet).
- `debug/text/provenance.json` — char-offset → page/bbox map.
- `debug/markdown/` — intermediate snapshots from Stage 02 post-processing.
- `debug/{{figures,tables,equations,references}}/` — structured artifacts
  that get rolled into `context-packet.json`.

## What was done to your paper

- Docling version: `{parser.get("version", "unknown")}`
- Formula enrichment: `{flags.get("formula_enrichment", "off")}` — math came through as {math_status}
- Code enrichment: `{flags.get("code_enrichment", "off")}` — code blocks {code_status}
- OCR: `{flags.get("ocr", "off")}` — {ocr_status}
- Pages processed: {manifest.get("page_count", 0)}
- Sections detected: {quality.get("section_count", 0)}
- Figures detected: {quality.get("figure_count", 0)}
- Tables detected: {quality.get("table_count", 0)}
- Equations detected: {quality.get("equation_count", 0)}

## Quality gates

{chr(10).join(gate_lines)}

## Reproducing this run

```bash
python scripts/01-parse.py "{manifest.get("input_pdf", "")}" --out <OUT_DIR> --formula-enrichment {flags.get("formula_enrichment", "off")} --code-enrichment {flags.get("code_enrichment", "off")} --ocr {flags.get("ocr", "off")}
python scripts/02-clean.py --out <OUT_DIR>
python scripts/03-packet.py --out <OUT_DIR>
```
"""

    (out_dir / "MANIFEST.md").write_text(md, encoding="utf-8")


def packet(out_dir: Path) -> None:
    """Run Stage 03."""
    log = setup_logging(out_dir)
    t0_total = time.monotonic()

    log.info("Stage 03 starting")

    build_context_packet(out_dir)
    cp_size = (out_dir / "context-packet.json").stat().st_size / 1024
    log.info(f"Wrote context-packet.json ({cp_size:.1f} KB)")

    write_manifest_md(out_dir)
    log.info("Wrote MANIFEST.md")

    log.info("Wrote quality-report.json")

    # Update manifest
    debug = out_dir / "debug"
    manifest = read_json(debug / "run-manifest.json")
    manifest["stages_completed"] = ["01-parse", "02-clean", "03-packet"]
    write_json(debug / "run-manifest.json", manifest)

    log.info(f"Stage 03 done ({time.monotonic() - t0_total:.1f}s total)")


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 03: Build packet")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    packet(args.out)


if __name__ == "__main__":
    main()
