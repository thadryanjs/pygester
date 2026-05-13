"""Stage 01: Parse PDF with Docling + rasterize pages."""
from __future__ import annotations

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
    return value == "on"


def parse_pdf(
    pdf_path: Path,
    out_dir: Path,
    parser_name: str = "docling",
    dpi: int = 200,
    max_pages: int | None = None,
    cache: bool = False,
    formula_enrichment: str = "off",
    code_enrichment: str = "off",
    ocr: str = "off",
) -> None:
    log = setup_logging(out_dir)
    t0_total = time.monotonic()

    log.info("Stage 01 starting")
    log.info(f"Config: formula_enrichment={formula_enrichment}, code_enrichment={code_enrichment}, ocr={ocr}, dpi={dpi}")

    debug = ensure_dir(out_dir / "debug")
    parser_dir = ensure_dir(debug / "parser")
    pages_dir = ensure_dir(out_dir / "pages")

    input_sha = sha256_file(pdf_path)
    manifest_path = debug / "run-manifest.json"

    # Cache check
    if cache and manifest_path.exists():
        manifest = read_json(manifest_path)
        cached_flags = manifest.get("flags", {})
        if (
            manifest.get("input_pdf_sha256") == input_sha
            and cached_flags.get("formula_enrichment") == formula_enrichment
            and cached_flags.get("code_enrichment") == code_enrichment
            and cached_flags.get("ocr") == ocr
            and cached_flags.get("dpi") == dpi
            and cached_flags.get("max_pages") == max_pages
        ):
            log.info("Cache hit: skipping Stage 01")
            return

    # Copy original PDF
    original_pdf = debug / "original.pdf"
    shutil.copy2(pdf_path, original_pdf)

    # Parse with Docling
    log.info("Loading Docling")
    t0_parse = time.monotonic()
    parser = DoclingParser()
    log.info(f"Loading complete ({time.monotonic() - t0_parse:.1f}s)")

    do_formula = _flag_on(formula_enrichment)
    do_code = _flag_on(code_enrichment)
    do_ocr = _flag_on(ocr)

    log.info(f"Parsing {pdf_path.name}")
    t0_parse = time.monotonic()
    parsed = parser.parse(
        pdf_path,
        max_pages=max_pages,
        do_formula_enrichment=do_formula,
        do_code_enrichment=do_code,
        do_ocr=do_ocr,
    )
    log.info(f"Parse complete ({time.monotonic() - t0_parse:.1f}s)")

    # Rasterize pages
    log.info(f"Rasterizing pages at {dpi} DPI")
    t0_raster = time.monotonic()
    doc = fitz.open(pdf_path)
    page_count = len(doc) if max_pages is None else min(len(doc), max_pages)
    for i in range(page_count):
        pix = doc[i].get_pixmap(dpi=dpi)
        pix.save(str(pages_dir / f"page_{i+1:04d}.png"))
    log.info(f"Rasterization complete ({time.monotonic() - t0_raster:.1f}s) — wrote {page_count} PNGs")

    # Write parser outputs
    write_json(parser_dir / "raw_output.json", parsed.raw_output)
    (parser_dir / "raw_output.md").write_text(parsed.markdown or "", encoding="utf-8")

    # Write manifest
    manifest = {
        "schema_version": "1",
        "tool_version": SKILL_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_pdf": str(pdf_path),
        "input_pdf_sha256": input_sha,
        "flags": {
            "formula_enrichment": formula_enrichment,
            "code_enrichment": code_enrichment,
            "ocr": ocr,
            "dpi": dpi,
            "max_pages": max_pages,
        },
        "parser": {
            "name": parser.name,
            "version": parser.version,
            "config": {
                "do_formula_enrichment": do_formula,
                "do_code_enrichment": do_code,
                "do_ocr": do_ocr,
            },
        },
        "page_count": page_count,
        "dpi": dpi,
        "stages_completed": ["01-parse"],
    }
    write_json(manifest_path, manifest)

    log.info(f"Stage 01 done ({time.monotonic() - t0_total:.1f}s total)")


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 01: Parse PDF")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--formula-enrichment", choices=["on", "off"], default="off")
    p.add_argument("--code-enrichment", choices=["on", "off"], default="off")
    p.add_argument("--ocr", choices=["on", "off"], default="off")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--cache", action="store_true")
    args = p.parse_args()

    parse_pdf(
        args.pdf,
        args.out,
        formula_enrichment=args.formula_enrichment,
        code_enrichment=args.code_enrichment,
        ocr=args.ocr,
        max_pages=args.max_pages,
        dpi=args.dpi,
        cache=args.cache,
    )


if __name__ == "__main__":
    main()
