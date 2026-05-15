"""Stage 02: Clean Docling output → paper.md + structured sidecars."""

import argparse
import logging
import re
import time
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

    frontmatter = f"""---
title: Docling Extract
source_sha256: {manifest.get("input_pdf_sha256", "")}
parser: {manifest.get("parser", {}).get("name", "docling")} {manifest.get("parser", {}).get("version", "")}
tool_version: {SKILL_VERSION}
run_at: {manifest.get("timestamp_utc", "")}
formula_enrichment: {flags.get("formula_enrichment", "false")}
ocr: {flags.get("ocr", "false")}
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


def _bbox_to_pixels(bbox: dict, dpi: int, page_h_px: int | None = None) -> tuple[int, int, int, int]:
    """Convert PDF bbox (points) to pixel coordinates with padding.
    
    Handles both BOTTOMLEFT (PDF default) and TOPLEFT coordinate origins.
    Adds 6px padding for breathing room around subscripts/superscripts.
    """
    scale = dpi / 72.0
    padding = 6  # pixels
    
    x0 = bbox["l"] * scale
    x1 = bbox["r"] * scale
    
    coord_origin = bbox.get("coord_origin", "BOTTOMLEFT")
    
    if coord_origin == "BOTTOMLEFT":
        # Flip Y: PDF measures from bottom, images from top
        if page_h_px is None:
            raise ValueError("page_h_px required for BOTTOMLEFT origin")
        y0 = page_h_px - (bbox["t"] * scale)
        y1 = page_h_px - (bbox["b"] * scale)
    else:
        # TOPLEFT: same coordinate system as image
        y0 = bbox["t"] * scale
        y1 = bbox["b"] * scale
    
    # Normalize (ensure left < right, top < bottom)
    x0, x1 = sorted((int(x0), int(x1)))
    y0, y1 = sorted((int(y0), int(y1)))
    
    # Apply padding (will be clamped by caller)
    return (x0 - padding, y0 - padding, x1 + padding, y1 + padding)


def extract_figures(parser_json: Path, pages_dir: Path, dpi: int, debug_dir: Path, out_dir: Path, log: logging.Logger) -> tuple[list[dict], int]:
    """Extract figure info from parser JSON. Returns (figures, count)."""
    data = read_json(parser_json)
    pictures = data.get("pictures", [])
    figures = []
    crops_written = 0
    crop_failures = 0

    ensure_dir(out_dir / "visuals" / "figures")

    for i, pic in enumerate(pictures, start=1):
        prov = pic.get("prov", [])
        if not prov:
            continue
        p = prov[0]
        page_no = p.get("page_no", 1)
        bbox = p.get("bbox", {})

        # Get caption from children
        captions = pic.get("captions", [])
        caption_text = None
        if captions:
            caption_ref = captions[0].get("$ref", "")
            for t in data.get("texts", []):
                if t.get("self_ref") == caption_ref:
                    caption_text = t.get("text", "")
                    break

        fig_id = f"fig-{i:03d}"
        crop_filename = f"figure_{i:03d}.png"
        image_path = None

        # Crop and save image
        page_png = pages_dir / f"page_{page_no:04d}.png"
        if page_png.exists():
            try:
                page_img = Image.open(page_png)
                page_h_px = page_img.height
                pixels = _bbox_to_pixels(bbox, dpi, page_h_px)
                
                # Clamp to page bounds
                pixels = (
                    max(0, pixels[0]),
                    max(0, pixels[1]),
                    min(page_img.width, pixels[2]),
                    min(page_h_px, pixels[3])
                )
                
                cropped = page_img.crop(pixels)
                cropped.save(out_dir / "visuals" / "figures" / crop_filename)
                crops_written += 1
            except Exception as e:
                log.warning(f"Crop failed for figure {i}: {e}")
                crop_failures += 1

        fig_entry = {
            "id": fig_id,
            "page": page_no,
            "bbox": [bbox.get("l", 0), bbox.get("b", 0), bbox.get("r", 0), bbox.get("t", 0)],
            "caption": caption_text,
            "image_path": f"visuals/figures/{crop_filename}",
        }
        figures.append(fig_entry)

    if crop_failures > 0:
        log.warning(f"Figure crop failures: {crop_failures}")
    
    log.info(f"Cropped {crops_written} figures")
    return figures, len(figures)


def extract_tables(parser_json: Path, debug_dir: Path) -> tuple[list[dict], int]:
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
            "rows": tbl.get("rows", 0),
            "cols": tbl.get("cols", 0),
        })

    return tables, len(tables)


def extract_code_blocks(parser_json: Path, pages_dir: Path, dpi: int, debug_dir: Path, out_dir: Path, log: logging.Logger) -> tuple[list[dict], int]:
    """Extract code block info from parser JSON. Returns (code_blocks, count)."""
    data = read_json(parser_json)
    texts = data.get("texts", [])
    code_blocks = [t for t in texts if t.get("label") == "code"]
    blocks = []
    crops_written = 0
    crop_failures = 0

    ensure_dir(out_dir / "visuals" / "code")

    for i, block in enumerate(code_blocks, start=1):
        prov = block.get("prov", [])
        if not prov:
            continue
        p = prov[0]
        page_no = p.get("page_no", 1)
        bbox = p.get("bbox", {})

        code_text = block.get("text", block.get("orig", ""))

        block_id = f"code-{i:03d}"
        crop_filename = f"code_{i:03d}.png"
        image_path = None

        # Crop and save image
        page_png = pages_dir / f"page_{page_no:04d}.png"
        if page_png.exists():
            try:
                page_img = Image.open(page_png)
                page_h_px = page_img.height
                pixels = _bbox_to_pixels(bbox, dpi, page_h_px)
                
                # Clamp to page bounds
                pixels = (
                    max(0, pixels[0]),
                    max(0, pixels[1]),
                    min(page_img.width, pixels[2]),
                    min(page_h_px, pixels[3])
                )
                
                cropped = page_img.crop(pixels)
                cropped.save(out_dir / "visuals" / "code" / crop_filename)
                image_path = f"visuals/code/{crop_filename}"
                crops_written += 1
            except Exception as e:
                log.warning(f"Crop failed for code block {i}: {e}")
                crop_failures += 1

        blocks.append({
            "id": block_id,
            "page": page_no,
            "bbox": [bbox.get("l", 0), bbox.get("b", 0), bbox.get("r", 0), bbox.get("t", 0)],
            "code": code_text,
            "image_path": image_path,
        })

    if crop_failures > 0:
        log.warning(f"Code block crop failures: {crop_failures}")
    
    if blocks:
        log.info(f"Cropped {crops_written} code blocks")
    return blocks, len(blocks)


def extract_equations(parser_json: Path, pages_dir: Path, dpi: int, debug_dir: Path, out_dir: Path, log: logging.Logger) -> tuple[list[dict], int]:
    """Extract equation info from parser JSON. Returns (equations, count)."""
    data = read_json(parser_json)
    texts = data.get("texts", [])
    equations = []
    crops_written = 0
    crop_failures = 0
    ensure_dir(out_dir / "visuals" / "equations")

    current_section_id = None
    last_prose_text = ""
    section_count = 0

    for block in texts:
        label = block.get("label")
        if label == "section_header":
            section_count += 1
            current_section_id = f"sec-{section_count:03d}"
            continue
        if label in ("text", "paragraph"):
            last_prose_text = block.get("text", "") or block.get("orig", "")
            continue
        if label != "formula":
            continue

        i = len(equations) + 1
        prov = block.get("prov", [])
        if not prov:
            continue
        p = prov[0]
        page_no = p.get("page_no", 1)
        bbox = p.get("bbox", {})

        # Enriched LaTeX if available; raw formula text otherwise.
        latex = block.get("text") or block.get("orig", "")

        eq_id = f"eq-{i:03d}"
        crop_filename = f"equation_{i:03d}.png"
        image_path = None

        # Crop and save image
        page_png = pages_dir / f"page_{page_no:04d}.png"
        if page_png.exists():
            try:
                page_img = Image.open(page_png)
                page_h_px = page_img.height
                pixels = _bbox_to_pixels(bbox, dpi, page_h_px)
                
                # Clamp to page bounds
                pixels = (
                    max(0, pixels[0]),
                    max(0, pixels[1]),
                    min(page_img.width, pixels[2]),
                    min(page_h_px, pixels[3])
                )
                
                cropped = page_img.crop(pixels)
                cropped.save(out_dir / "visuals" / "equations" / crop_filename)
                image_path = f"visuals/equations/{crop_filename}"
                crops_written += 1
            except Exception as e:
                log.warning(f"Crop failed for equation {i}: {e}")
                crop_failures += 1

        equations.append({
            "id": eq_id,
            "page": page_no,
            "bbox": [bbox.get("l", 0), bbox.get("b", 0), bbox.get("r", 0), bbox.get("t", 0)],
            "latex": latex,
            "image_path": image_path,
            "number": None,  # Docling doesn't provide equation numbers
            "section_id": current_section_id,
            "preceding_prose": last_prose_text,
        })

    if crop_failures > 0:
        log.warning(f"Equation crop failures: {crop_failures}")
    
    log.info(f"Cropped {crops_written} equations")
    return equations, len(equations)


def extract_references(parser_json: Path, debug_dir: Path) -> tuple[list[dict], int]:
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

    paper_md = out_dir / "paper.md"
    paper_exists = paper_md.exists() and paper_md.stat().st_size > 0

    gates = {
        "paper_md_exists": paper_exists,
        "has_references_section": counts.get("references", 0) > 0,
        "raster_page_count_ok": page_count == manifest.get("page_count", 0),
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

    markdown_dir = ensure_dir(debug / "intermediate" / "markdown")
    (markdown_dir / "01-with-frontmatter.md").write_text(with_frontmatter, encoding="utf-8")
    (out_dir / "paper.md").write_text(with_frontmatter, encoding="utf-8")

    log.info("Walking Docling AST")
    sections = extract_sections(parser_md) if parser_md.exists() else []
    figures, fig_count = extract_figures(parser_dir / "raw_output.json", pages_dir, dpi, debug, out_dir, log)
    tables, tbl_count = extract_tables(parser_dir / "raw_output.json", debug)
    equations, eq_count = extract_equations(parser_dir / "raw_output.json", pages_dir, dpi, debug, out_dir, log)
    code_blocks, code_count = extract_code_blocks(parser_dir / "raw_output.json", pages_dir, dpi, debug, out_dir, log)
    references, ref_count = extract_references(parser_dir / "raw_output.json", debug)

    counts = {
        "sections": len(sections),
        "figures": fig_count,
        "tables": tbl_count,
        "equations": eq_count,
        "references": ref_count,
    }

    log.info(f"Wrote {eq_count} equations, {fig_count} figures, {tbl_count} tables, {ref_count} references")

    # Write sidecars only if non-empty
    text_dir = ensure_dir(debug / "intermediate" / "text")
    write_json(text_dir / "sections.json", sections)
    (text_dir / "plaintext.txt").write_text(normalized, encoding="utf-8")

    if figures:
        figures_dir = ensure_dir(out_dir / "visuals" / "figures")
        write_json(figures_dir / "figures.json", figures)

    if tables:
        tables_dir = ensure_dir(out_dir / "tables")
        write_json(tables_dir / "tables.json", tables)

    if equations:
        equations_dir = ensure_dir(out_dir / "visuals" / "equations")
        write_json(equations_dir / "equations.json", equations)

    if references:
        references_dir = ensure_dir(out_dir / "references")
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
