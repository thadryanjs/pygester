"""Stage 03: Compose context-packet.json, technical-summary.md, MANIFEST.md, and final deliverables."""

import argparse
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from common import read_json, write_json, setup_logging, ensure_dir

SKILL_VERSION = "0.1.0"


def build_context_packet(out_dir: Path) -> None:
    """Build context packet from artifacts."""
    debug = out_dir / "debug"
    manifest = read_json(debug / "run-manifest.json")
    quality = read_json(out_dir / "quality-report.json")

    # Load sidecars (visuals and structured data are in core output)
    sections = read_json(debug / "sections.json") if (debug / "sections.json").exists() else []

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

    paper_profile = extract_paper_profile(debug, manifest)

    # Build packet
    packet = {
        "schema_version": "1",
        "paper_profile": paper_profile,
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


def extract_paper_profile(debug: Path, manifest: dict) -> dict:
    """Extract conservative paper profile from Docling output."""
    profile = {
        "title": None,
        "authors": [],
        "page_count": manifest.get("page_count", 0),
        "input_pdf_sha256": manifest.get("input_pdf_sha256", ""),
        "parser": manifest.get("parser", {}),
        "tool_version": SKILL_VERSION,
    }

    raw_path = debug / "parser" / "raw_output.json"
    if not raw_path.exists():
        return profile

    texts = read_json(raw_path).get("texts", [])
    title_idx = None
    for i, block in enumerate(texts):
        if block.get("label") == "section_header":
            title = (block.get("text") or block.get("orig") or "").strip()
            if title:
                profile["title"] = title
                title_idx = i
                break

    if title_idx is None:
        return profile

    authors = []
    for block in texts[title_idx + 1:]:
        label = block.get("label")
        text = (block.get("text") or block.get("orig") or "").strip()
        if not text:
            continue
        if label == "section_header":
            break
        if label not in ("text", "paragraph"):
            continue
        if text.lower().startswith("abstract"):
            break
        authors.append(text)

    if authors:
        profile["authors"] = authors

    return profile


def write_technical_summary(out_dir: Path, packet: dict, manifest: dict, enrichment_on: bool) -> Path:
    """Write technical-summary.md to OUT_DIR."""
    summary_path = out_dir / "technical-summary.md"
    profile = packet.get("paper_profile", {})
    title = profile.get("title")
    if not title or title == "Unknown":
        title = "(title not detected)"
    authors = profile.get("authors") or []
    author_str = ", ".join(authors) if authors else "unknown"
    sha = manifest.get("input_pdf_sha256", "")[:12]
    timestamp = datetime.now(timezone.utc).isoformat()

    parts = [
        f"# Technical summary — {title}",
        "",
        f"Authors: {author_str}",
        f"Source: {manifest.get('input_pdf', '')} (SHA {sha})",
        f"Generated: {timestamp}",
        f"Formula enrichment: {str(enrichment_on).lower()}",
        "",
    ]

    abstract = find_abstract(packet, out_dir / "paper.md")
    if abstract:
        parts.extend(["## Abstract", "", abstract, ""])

    parts.extend(["## Equations", ""])
    equations = packet.get("equations", [])
    if not equations:
        parts.extend(["_No equations detected in this document._", ""])
    else:
        parts.extend(render_equation_groups(equations, packet, enrichment_on))

    text = "\n".join(parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    summary_path.write_text(text, encoding="utf-8")
    return summary_path


def find_abstract(packet: dict, paper_md: Path) -> str | None:
    """Return abstract text when available."""
    for section in packet.get("sections", []):
        if section.get("label") == "abstract":
            return section.get("text", "").strip() or None

    prose_blocks = packet.get("title_to_first_section_prose", [])
    if prose_blocks:
        text = "\n\n".join(b.strip() for b in prose_blocks if b.strip()).strip()
        if text:
            return text

    return extract_abstract_from_markdown(paper_md)


def extract_abstract_from_markdown(path: Path) -> str | None:
    """Fallback: extract Abstract section from paper.md if present."""
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


def render_equation_groups(equations: list[dict], packet: dict, enrichment_on: bool) -> list[str]:
    """Render equations grouped by section when section_id exists."""
    out = []
    prev_section_id = object()
    sections_by_id = {s.get("id"): s for s in packet.get("sections", []) if s.get("id")}

    for i, eq in enumerate(equations, start=1):
        section_id = eq.get("section_id")
        page = eq.get("page", "?")

        if section_id != prev_section_id:
            section = sections_by_id.get(section_id, {})
            heading = section.get("heading") or "(unsectioned)"
            out.extend([f"### From \"{heading}\" (p. {page})", ""])
            prev_section_id = section_id

        text = (eq.get("text") or eq.get("latex") or "").strip()
        if text:
            if enrichment_on:
                out.extend(["$$", text, "$$"])
            else:
                out.extend(["```", text, "```"])
        else:
            image_path = eq.get("image_path")
            if image_path:
                out.append(f"![Equation {i}]({image_path})")
            else:
                out.append("_No formula text extracted._")

        label = eq.get("number") or str(i)
        context = extract_equation_context(eq)
        if context:
            out.append(f"*Equation ({label})* — {context}")
        else:
            out.append(f"*Equation ({label})*")
        out.append("")

    return out


def extract_equation_context(eq: dict) -> str | None:
    """Up to 25-word hint from prose preceding equation."""
    prose = eq.get("preceding_prose", "")
    if not prose:
        return None
    sentences = [s.strip() for s in re.split(r"[.!?]+", prose) if s.strip()]
    if not sentences:
        return None
    last = sentences[-1]
    last = re.sub(r"^[\s,;:—–-]+", "", last)
    last = re.sub(r"[\s,;:]+$", "", last)
    words = last.split()
    if len(words) > 25:
        last = " ".join(words[:25]) + "…"
    return last or None


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
- **`technical-summary.md`** — abstract + every equation, grouped by section.
  For math-focused chats: equation translation, derivation checks, code
  generation. Smaller than `paper.md`, faster to paste.
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
- `paper-text.md` — canonical text without markdown formatting.
- `debug/sections.json` — section tree (already in context-packet).
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
- Equations in technical summary: {eq_count}{" — no equations found in this document" if eq_count == 0 else ""}

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
    summary_exists = summary_path.exists() and summary_path.stat().st_size > 0
    summary_text = summary_path.read_text(encoding="utf-8") if summary_exists else ""
    has_equation_blocks = ("$$" in summary_text) if enrichment_on else ("```" in summary_text)
    abstract = find_abstract(packet, out_dir / "paper.md")

    quality = read_json(out_dir / "quality-report.json")
    gates = quality.setdefault("gates", {})
    gates["technical_summary_exists"] = summary_exists
    gates["technical_summary_has_equations"] = has_equation_blocks
    quality["technical_summary_exists"] = summary_exists
    quality["technical_summary_has_equations"] = has_equation_blocks
    counts = quality.setdefault("counts", {})
    counts["equations_in_technical_summary"] = eq_count
    if eq_count != len(packet.get("equations", [])):
        warnings = quality.setdefault("warnings", [])
        warnings.append("equations_in_technical_summary does not match equations.json count")
    if not abstract:
        warnings = quality.setdefault("warnings", [])
        if "abstract_not_found" not in warnings:
            warnings.append("abstract_not_found")
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
