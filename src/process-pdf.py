#!/usr/bin/env python3
"""Run all stages: parse → clean → packet."""

import argparse
import time
from pathlib import Path

from parse import parse_pdf
from clean import clean
from packet import packet


def main() -> None:
    p = argparse.ArgumentParser(description="digest-technical-paper: full pipeline")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--formula-enrichment", choices=["true", "false"], default="false")
    p.add_argument("--ocr", choices=["true", "false"], default="false")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--dpi", type=int, default=200)
    args = p.parse_args()

    t0_total = time.monotonic()
    out_dir = args.out

    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage: parse
    if not (out_dir / "debug" / "parser" / "raw_output.json").exists():
        print(f"[{time.strftime('%H:%M:%S')}] Running parse...")
        parse_pdf(
            args.pdf,
            args.out,
            formula_enrichment=args.formula_enrichment,
            ocr=args.ocr,
            max_pages=args.max_pages,
            dpi=args.dpi,
        )
    else:
        print(f"[{time.strftime('%H:%M:%S')}] parse complete, skipping")

    # Stage: clean
    if not (out_dir / "paper.md").exists():
        print(f"[{time.strftime('%H:%M:%S')}] Running clean...")
        clean(args.out)
    else:
        print(f"[{time.strftime('%H:%M:%S')}] clean complete, skipping")

    # Stage: packet
    if not (out_dir / "context-packet.json").exists():
        print(f"[{time.strftime('%H:%M:%S')}] Running packet...")
        packet(args.out)
    else:
        print(f"[{time.strftime('%H:%M:%S')}] packet complete, skipping")

    elapsed = time.monotonic() - t0_total
    print(f"[{time.strftime('%H:%M:%S')}] Total elapsed: {elapsed:.1f}s")
    print(f"[{time.strftime('%H:%M:%S')}] Pipeline complete")


if __name__ == "__main__":
    main()
