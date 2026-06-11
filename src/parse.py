"""parse stage: Parse PDF with Docling + rasterize pages."""

import argparse
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz

from common import ensure_dir, read_json, sha256_file, write_json, setup_logging
from parsers.docling_parser import DoclingParser

SKILL_VERSION = "0.1.0"


def _flag_on(value: str) -> bool:
    return value == "true"


def parse_pdf(
    pdf_path: Path,
    out_dir: Path,
    dpi: int = 200,
    max_pages: int | None = None,
    formula_enrichment: str = "false",
    ocr: str = "false",
) -> None:
    log = setup_logging(out_dir)
    t0_total = time.monotonic()

    log.info("parse stage starting")
    log.info(f"Config: formula_enrichment={formula_enrichment}, ocr={ocr}, dpi={dpi}, max_pages={max_pages}")

    debug = ensure_dir(out_dir / "debug")
    parser_dir = ensure_dir(debug / "parser")
    pages_dir = ensure_dir(out_dir / "pages")

    input_sha = sha256_file(pdf_path)
    manifest_path = debug / "run-manifest.json"

    # Copy original PDF
    original_pdf = debug / "original.pdf"
    shutil.copy2(pdf_path, original_pdf)

    # Parse with Docling
    log.info("Loading Docling")
    t0_parse = time.monotonic()
    parser = DoclingParser()
    log.info(f"Loading complete ({time.monotonic() - t0_parse:.1f}s)")

    do_formula = _flag_on(formula_enrichment)
    do_ocr = _flag_on(ocr)

    log.info(f"Parsing {pdf_path.name}")
    t0_parse = time.monotonic()
    parsed = parser.parse(
        pdf_path,
        max_pages=max_pages,
        do_formula_enrichment=do_formula,
        do_ocr=do_ocr,
    )
    log.info(f"Parse complete ({time.monotonic() - t0_parse:.1f}s)")

    # Write parser outputs BEFORE rasterization (protect expensive enrichment work)
    write_json(parser_dir / "raw_output.json", parsed.raw_output)
    (parser_dir / "raw_output.md").write_text(parsed.markdown or "", encoding="utf-8")

    # Rasterize pages
    log.info(f"Rasterizing pages at {dpi} DPI")
    pages_dir.mkdir(parents=True, exist_ok=True)
    t0_raster = time.monotonic()
    doc = fitz.open(pdf_path)
    page_count = len(doc) if max_pages is None else min(len(doc), max_pages)
    for i in range(page_count):
        pix = doc[i].get_pixmap(dpi=dpi)
        pix.save(str(pages_dir / f"page_{i+1:04d}.png"))
    log.info(f"Rasterization complete ({time.monotonic() - t0_raster:.1f}s) — wrote {page_count} PNGs")

    # Write manifest
    manifest = {
        "schema_version": "1",
        "tool_version": SKILL_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_pdf": str(pdf_path),
        "input_pdf_sha256": input_sha,
        "flags": {
            "formula_enrichment": formula_enrichment,
            "ocr": ocr,
            "dpi": dpi,
            "max_pages": max_pages,
        },
        "parser": {
            "name": parser.name,
            "version": parser.version,
            "config": {
                "do_formula_enrichment": do_formula,
                "do_ocr": do_ocr,
            },
        },
        "page_count": page_count,
        "dpi": dpi,
        "stages_completed": ["parse"],
    }
    write_json(manifest_path, manifest)

    log.info(f"parse stage done ({time.monotonic() - t0_total:.1f}s total)")


def main() -> None:
    p = argparse.ArgumentParser(description="parse stage: Parse PDF")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--formula-enrichment", choices=["true", "false"], default="false")
    p.add_argument("--ocr", choices=["true", "false"], default="false")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    parse_pdf(
        args.pdf,
        args.out,
        formula_enrichment=args.formula_enrichment,
        ocr=args.ocr,
        max_pages=args.max_pages,
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
