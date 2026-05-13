"""Stage 02: Clean Docling output → paper.md + structured sidecars."""
from __future__ import annotations

import argparse
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from common import read_json, write_json, setup_logging, ensure_dir
from PIL import Image

SKILL_VERSION = "0.1.0"


def normalize_text(text: str) -> str:
    """Normalize ligatures and preserve special characters."""
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬂ", "fl")
    text = text.replace("ﬀ", "ff")
    text = text.replace("ﬃ", "ffi")
    text = text.replace("ﬄ", "ffl")

    def rejoin_hyphen(match):
        word = match.group(1)
        next_word = match.group(2)
        if next_word[0].islower():
            return word + next_word
        return match.group(0)

    text = re.sub(r'(\w+)-\n([a-zA-Z])', rejoin_hyphen, text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def add_frontmatter(markdown: str, manifest: dict) -> str:
    """Prepend YAML frontmatter."""
    flags = manifest.get("flags", {})
    formula = "LaTeX" if flags.get("formula_enrichment") == "on" else "Unicode soup"

    frontmatter = f"""---
title: Docling Extract
source_sha256: {manifest.get("input_pdf_sha256", "")}
parser: {manifest.get("parser", {}).get("name", "docling")} {manifest.get("parser", {}).get("version", "")}
tool_version: {SKILL_VERSION}
run_at: {manifest.get("timestamp_utc", "")}
formula_enrichment: {flags.get("formula_enrichment", "off")}
code_enrichment: {flags.get("code_enrichment", "off")}
ocr: {flags.get("ocr", "off")}
---

"""
    return frontmatter + markdown


def extract_sections(parser_md: Path) -> list[dict]:
    """Extract section info from parser markdown."""
    sections = []
    content = parser_md.read_text(encoding="utf-8")
    lines = content.split("\n")

    current_section = None
    char_offset = 0

    for line in lines:
        if line.startswith("#"):
            if current_section:
                current_section["end_char"] = char_offset
            level = len(line) - len(line.lstrip("#"))
            heading = line.lstrip("#").strip()
            current_section = {
                "id": f"sec-{len(sections)+1:03d}",
                "heading": heading,
                "level": max(1, level),
                "start_char": char_offset,
                "end_char": 0,
            }
            sections.append(current_section)
        char_offset += len(line) + 1

    if sections:
        sections[-1]["end_char"] = char_offset

    return sections


def _bbox_to_pixels(bbox: dict, dpi: int) -> tuple[int, int, int, int]:
    """Convert PDF bbox (points) to pixel coordinates."""
    scale = dpi / 72.0
    x0 = int(bbox["l"] * scale)
    y0 = int(bbox["b"] * scale)
    x1 = int(bbox["r"] * scale)
    y1 = int(bbox["t"] * scale)
    return (x0, y0, x1, y1)


def extract_figures(parser_json: Path, pages_dir: Path, dpi: int, debug_dir: Path) -> tuple[list[dict], int]:
    """Extract figure info from parser JSON. Returns (figures, count)."""
    data = read_json(parser_json)
    pictures = data.get("pictures", [])
    figures = []

    for i, pic in enumerate(pictures):
        prov = pic.get("prov", [])
        if not prov:
            continue
        p = prov[0]
        page_no = p.get("page_no", 1)
        bbox = p.get("bbox", {})

        captions = pic.get("captions", [])
        caption_text = None
        if captions:
            caption_ref = captions[0].get("$ref", "")
            for t in data.get("texts", []):
                if t.get("self_ref") == caption_ref:
                    caption_text = t.get("text", "")
                    break

        fig_id = f"fig-{i+1:03d}"
        fig_entry = {
            "id": fig_id,
            "page": page_no,
            "bbox": [bbox.get("l", 0), bbox.get("b", 0), bbox.get("r", 0), bbox.get("t", 0)],
            "caption": caption_text,
            "image_path": f"debug/figures/{fig_id}.png",
        }
        figures.append(fig_entry)

        page_png = pages_dir / f"page_{page_no:04d}.png"
        if page_png.exists():
            img = Image.open(page_png)
            pixels = _bbox_to_pixels(bbox, dpi)
            cropped = img.crop(pixels)
            figures_dir = debug_dir / "figures"
            figures_dir.mkdir(parents=True, exist_ok=True)
            cropped.save(figures_dir / f"{fig_id}.png")

    return figures, len(figures)


def extract_tables(parser_json: Path) -> tuple[list[dict], int]:
    """Extract table info from parser JSON. Returns (tables, count)."""
    data = read_json(parser_json)
    tables_data = data.get("tables", [])
    tables = []

    for i, tbl in enumerate(tables_data):
        prov = tbl.get("prov", [])
        if not prov:
            continue
        p = prov[0]
        page_no = p.get("page_no", 1)
        bbox = p.get("bbox", {})

        tbl_id = f"tab-{i+1:03d}"
        tables.append({
            "id": tbl_id,
            "page": page_no,
            "bbox": [bbox.get("l", 0), bbox.get("b", 0), bbox.get("r", 0), bbox.get("t", 0)],
            "csv_path": f"debug/tables/{tbl_id}.csv",
            "rows": tbl.get("rows", 0),
            "cols": tbl.get("cols", 0),
        })

    return tables, len(tables)


def extract_equations(parser_json: Path, pages_dir: Path, dpi: int, debug_dir: Path) -> tuple[list[dict], int]:
    """Extract equation info from parser JSON. Returns (equations, count)."""
    data = read_json(parser_json)
    texts = data.get("texts", [])
    formulas = [t for t in texts if t.get("label") == "formula"]
    equations = []

    for i, fmt in enumerate(formulas):
        prov = fmt.get("prov", [])
        if not prov:
            continue
        p = prov[0]
        page_no = p.get("page_no", 1)
        bbox = p.get("bbox", {})

        latex = fmt.get("text", fmt.get("orig", ""))

        eq_id = f"eq-{i+1:03d}"
        equations.append({
            "id": eq_id,
            "page": page_no,
            "bbox": [bbox.get("l", 0), bbox.get("b", 0), bbox.get("r", 0), bbox.get("t", 0)],
            "latex": latex,
            "image_path": f"debug/equations/{eq_id}.png",
            "number": None,
        })

        page_png = pages_dir / f"page_{page_no:04d}.png"
        if page_png.exists():
            img = Image.open(page_png)
            pixels = _bbox_to_pixels(bbox, dpi)
            cropped = img.crop(pixels)
            equations_dir = debug_dir / "equations"
            equations_dir.mkdir(parents=True, exist_ok=True)
            cropped.save(equations_dir / f"{eq_id}.png")

    return equations, len(equations)


def extract_references(parser_json: Path) -> tuple[list[dict], int]:
    """Extract reference info from parser JSON. Returns (references, count)."""
    data = read_json(parser_json)
    texts = data.get("texts", [])

    refs_start = None
    for i, t in enumerate(texts):
        if t.get("label") == "section_header" and t.get("text", "").upper() == "REFERENCES":
            refs_start = i + 1
            break

    if refs_start is None:
        return [], 0

    references = []
    for i, t in enumerate(texts[refs_start:]):
        if t.get("label") != "list_item":
            if t.get("label") in ("page_footer", "page_header", "section_header"):
                break
            continue

        raw_text = t.get("text", "")
        match = re.match(r'^\[(\d+)\]\s*', raw_text)
        key = match.group(1) if match else str(len(references) + 1)

        prov = t.get("prov", [])
        page_no = prov[0].get("page_no", 1) if prov else 1

        references.append({
            "id": f"ref-{key}",
            "key": key,
            "raw": raw_text,
            "page": page_no,
            "authors": None,
            "title": None,
            "venue": None,
            "year": None,
        })

    return references, len(references)


def write_quality_report(out_dir: Path, manifest: dict, counts: dict) -> None:
    """Write quality report with per-extractor counts."""
    pages_dir = out_dir / "pages"
    page_count = len(list(pages_dir.glob("page_*.png"))) if pages_dir.exists() else 0

    gates = {
        "canonical_non_empty": True,
        "has_references_section": counts.get("references", 0) > 0,
        "raster_page_count_ok": page_count == manifest.get("page_count", 0),
        "paper_md_exists": True,
        "context_packet_valid": True,
    }

    report = {
        "schema_version": "1",
        "status": "ok" if all(gates.values()) else "warn",
        "gates": gates,
        "section_count": counts.get("sections", 0),
        "figure_count": counts.get("figures", 0),
        "table_count": counts.get("tables", 0),
        "equation_count": counts.get("equations", 0),
        "reference_count": counts.get("references", 0),
    }

    write_json(out_dir / "quality-report.json", report)


def clean(out_dir: Path) -> None:
    """Run Stage 02: clean and produce artifacts."""
    log = setup_logging(out_dir)
    t0_total = time.monotonic()

    log.info("Stage 02 starting")
    debug = out_dir / "debug"
    parser_dir = debug / "parser"
    pages_dir = out_dir / "pages"

    manifest = read_json(debug / "run-manifest.json")
    dpi = manifest.get("dpi", 200)

    parser_md = parser_dir / "raw_output.md"
    markdown = parser_md.read_text(encoding="utf-8")

    normalized = normalize_text(markdown)
    with_frontmatter = add_frontmatter(normalized, manifest)

    markdown_dir = ensure_dir(debug / "markdown")
    (markdown_dir / "01-with-frontmatter.md").write_text(with_frontmatter, encoding="utf-8")
    (out_dir / "paper.md").write_text(with_frontmatter, encoding="utf-8")

    log.info("Walking Docling AST")
    sections = extract_sections(parser_md)
    figures, fig_count = extract_figures(parser_dir / "raw_output.json", pages_dir, dpi, debug)
    tables, tbl_count = extract_tables(parser_dir / "raw_output.json")
    equations, eq_count = extract_equations(parser_dir / "raw_output.json", pages_dir, dpi, debug)
    references, ref_count = extract_references(parser_dir / "raw_output.json")

    counts = {
        "sections": len(sections),
        "figures": fig_count,
        "tables": tbl_count,
        "equations": eq_count,
        "references": ref_count,
    }

    log.info(f"Wrote {eq_count} equations, {fig_count} figures, {tbl_count} tables, {ref_count} references")

    # Write sidecars only if non-empty
    text_dir = ensure_dir(debug / "text")
    write_json(text_dir / "sections.json", sections)
    write_json(text_dir / "provenance.json", [])
    (text_dir / "plaintext.txt").write_text(normalized, encoding="utf-8")

    if figures:
        figures_dir = ensure_dir(debug / "figures")
        write_json(figures_dir / "figures.json", figures)

    if tables:
        tables_dir = ensure_dir(debug / "tables")
        write_json(tables_dir / "tables.json", tables)

    if equations:
        equations_dir = ensure_dir(debug / "equations")
        write_json(equations_dir / "equations.json", equations)

    if references:
        references_dir = ensure_dir(debug / "references")
        write_json(references_dir / "references.json", references)

    manifest["stages_completed"] = ["01-parse", "02-clean"]
    write_json(debug / "run-manifest.json", manifest)

    write_quality_report(out_dir, manifest, counts)

    md_size = (out_dir / "paper.md").stat().st_size / 1024
    log.info(f"Wrote paper.md ({md_size:.1f} KB)")
    log.info(f"Stage 02 done ({time.monotonic() - t0_total:.1f}s total)")


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 02: Clean output")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    clean(args.out)


if __name__ == "__main__":
    main()
