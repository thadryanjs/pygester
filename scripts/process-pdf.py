#!/usr/bin/env python3
"""Run all stages: 01-parse → 02-clean → 03-packet."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="digest-technical-paper: full pipeline")
    p.add_argument("pdf", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--formula-enrichment", choices=["on", "off"], default="off")
    p.add_argument("--code-enrichment", choices=["on", "off"], default="off")
    p.add_argument("--ocr", choices=["on", "off"], default="off")
    p.add_argument("--max-pages", type=int, default=None)
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--cache", action="store_true")
    args = p.parse_args()

    t0_total = time.monotonic()
    scripts_dir = Path(__file__).parent

    # Stage 01
    stage1_args = [
        sys.executable,
        str(scripts_dir / "01-parse.py"),
        str(args.pdf),
        "--out",
        str(args.out),
        "--formula-enrichment",
        args.formula_enrichment,
        "--code-enrichment",
        args.code_enrichment,
        "--ocr",
        args.ocr,
        "--dpi",
        str(args.dpi),
    ]
    if args.max_pages is not None:
        stage1_args.extend(["--max-pages", str(args.max_pages)])
    if args.cache:
        stage1_args.append("--cache")
    subprocess.run(stage1_args, check=True)

    # Stage 02
    subprocess.run(
        [sys.executable, str(scripts_dir / "02-clean.py"), "--out", str(args.out)],
        check=True,
    )

    # Stage 03
    subprocess.run(
        [sys.executable, str(scripts_dir / "03-packet.py"), "--out", str(args.out)],
        check=True,
    )

    print(f"[{time.strftime('%H:%M:%S')}] Total elapsed: {time.monotonic() - t0_total:.1f}s")


if __name__ == "__main__":
    main()
