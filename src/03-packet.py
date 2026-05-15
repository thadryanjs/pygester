"""Stage 03: Compose context-packet.json, technical-summary.md, MANIFEST.md, and final deliverables."""

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

    # Load sidecars (visuals and structured data are in core output)
    sections = read_json(debug / "intermediate" / "text" / "sections.json") if (debug / "intermediate" / "text" / "sections.json").exists() else []

    figures = []
    if (out_dir / "visuals" / "figures" / "figures.json").exists():
        figures = read_json(out_dir / "visuals" / "figures" / "figures.json")

    tables = []
    if (out_dir / "tables" / "tables.json").exists():
        tables = read_json(out_dir / "tables" / "tables.json")

    equations = []
    if (out_dir / "visuals" / "equations" / "equations.json").exists():
        equations = read_json(out_dir / "visuals" / "equations" / "equations.json")

    references = []
    if (out_dir / "references" / "references.json").exists():
        references = read_json(out_dir / "references" / "references.json")

    code_blocks = []
    if (out_dir / "visuals" / "code" / "code.json").exists():
        code_blocks = read_json(out_dir / "visuals" / "code" / "code.json")

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
        "code_blocks": code_blocks,
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


def write_technical_summary(out_dir: Path, packet: dict, manifest: dict, enrichment_on: bool) -> Path:
    """Write minimal technical-summary.md to OUT_DIR."""
    summary_path = out_dir / "technical-summary.md"
    paper_md = out_dir / "paper.md"
    equations = packet.get("equations", [])

    parts = [
        "# Technical summary",
        "",
        f"Source: {manifest.get('input_pdf', '')}",
        f"Formula enrichment: {str(enrichment_on).lower()}",
        "",
    ]

    abstract = extract_abstract_from_markdown(paper_md)
    if abstract:
        parts.extend(["## Abstract", "", abstract, ""])

    parts.extend(["## Equations", ""])
    if not equations:
        parts.extend(["_No equations detected._", ""])
    else:
        for i, eq in enumerate(equations, start=1):
            page = eq.get("page", "?")
            text = (eq.get("latex") or "").strip()
            image_path = eq.get("image_path")

            parts.append(f"### Equation {i} (p. {page})")
            parts.append("")
            if text:
                fence = "$$" if enrichment_on else "```"
                parts.extend([fence, text, fence, ""])
            elif image_path:
                parts.extend([f"![Equation {i}]({image_path})", ""])
            else:
                parts.extend(["_No formula text extracted._", ""])

    summary_path.write_text("\n".join(parts), encoding="utf-8")
    return summary_path


def extract_abstract_from_markdown(path: Path) -> str | None:
    """Extract Abstract section from paper.md if present."""
    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lstrip("#").strip().lower() == "abstract":
            start = i + 1
            break
    if start is None:
        return None

    out = []
    for line in lines[start:]:
        if line.startswith("#"):
            break
        out.append(line)

    abstract = "\n".join(out).strip()
    return abstract or None


def write_manifest_md(out_dir: Path, eq_count: int) -> None:
    """Write human-readable MANIFEST.md."""
    debug = out_dir / "debug"
    manifest = read_json(debug / "run-manifest.json")
    quality = read_json(out_dir / "quality-report.json")

    flags = manifest.get("flags", {})
    parser = manifest.get("parser", {})
    config = parser.get("config", {})

    math_status = "LaTeX" if config.get("do_formula_enrichment") else "Unicode (formula enrichment off)"
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
  Math is {math_status}.
- **`technical-summary.md`** — abstract + every detected equation.
  Small math-focused digest for equation translation, derivation checks, and code generation.
- **`context-packet.json`** — structured metadata: sections with page ranges,
  figures, tables, equations, references. The thing to paste alongside `paper.md`
  when an LLM needs to know what's on each page.
- **`pages/page_NNNN.png`** — one rasterized image per page ({manifest.get("page_count", 0)} total).
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
- Equations detected: {quality.get("equation_count", 0)}{" — no equations found in this document" if eq_count == 0 else " (in technical-summary.md)"}

## Quality gates

{chr(10).join(gate_lines)}

## Reproducing this run

```bash
python src/01-parse.py "{manifest.get("input_pdf", "")}" --out <OUT_DIR> --formula-enrichment {flags.get("formula_enrichment", "false")} --code-enrichment {flags.get("code_enrichment", "false")} --ocr {flags.get("ocr", "false")}
python src/02-clean.py --out <OUT_DIR>
python src/03-packet.py --out <OUT_DIR>
```
"""

    (out_dir / "MANIFEST.md").write_text(md, encoding="utf-8")


def packet(out_dir: Path) -> None:
    """Run Stage 03."""
    log = setup_logging(out_dir)
    t0_total = time.monotonic()

    log.info("Stage 03 starting")

    debug = out_dir / "debug"
    manifest = read_json(debug / "run-manifest.json")
    flags = manifest.get("flags", {})
    enrichment_on = flags.get("formula_enrichment", "false") == "true"

    # 1. Build context packet
    build_context_packet(out_dir)
    packet = read_json(out_dir / "context-packet.json")
    cp_size = (out_dir / "context-packet.json").stat().st_size / 1024
    log.info(f"Wrote context-packet.json ({cp_size:.1f} KB)")

    # 2. Write technical summary
    eq_count = len(packet.get("equations", []))
    summary_path = write_technical_summary(out_dir, packet, manifest, enrichment_on)
    summary_size = summary_path.stat().st_size / 1024
    log.info(f"Wrote technical-summary.md ({summary_size:.1f} KB, {eq_count} equations)")

    # 3. Update quality report
    has_equations = eq_count > 0
    summary_exists = summary_path.exists() and summary_path.stat().st_size > 0
    quality = read_json(out_dir / "quality-report.json")
    quality["technical_summary_exists"] = summary_exists
    quality["technical_summary_has_equations"] = has_equations
    quality["equations_in_technical_summary"] = eq_count
    write_json(out_dir / "quality-report.json", quality)
    log.info("Wrote quality-report.json")

    # 4. Write manifest
    write_manifest_md(out_dir, eq_count)
    log.info("Wrote MANIFEST.md")

    # Update manifest
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
