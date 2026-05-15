# spec-enhancements-1.md

Add `technical-summary.md` as a top-level deliverable: abstract + every equation grouped by section, intended for math-focused chats with LLMs (equation translation, derivation checks, code generation).

Written for an implementer who has the spec loaded. This doc covers the **how**.

## Where it lives

Stage 03 (`src/03-packet.py`). Written alongside `context-packet.json`, `quality-report.json`, and `MANIFEST.md`.

```
OUT_DIR/
├── MANIFEST.md
├── paper.md
├── technical-summary.md      ← new
├── context-packet.json
├── quality-report.json
├── pages/
├── visuals/
├── references/
└── debug/
```

## Generation order within Stage 03

1. `context-packet.json` (others reference its data)
2. `technical-summary.md` (uses packet's section + equation arrays)
3. `quality-report.json` (uses all of the above to populate gates)
4. `MANIFEST.md` (uses everything; written last)

All four derive from the same inputs (`debug/intermediate/text/sections.json`, `visuals/equations/equations.json`, paper profile from manifest). Load once, pass to each writer.

## The output format

```markdown
# Technical summary — <paper title>

Authors: <comma-joined authors, or "unknown">
Source: <input filename> (SHA <first 12 chars of input_pdf_sha256>)
Generated: <ISO 8601 timestamp, UTC>
Formula enrichment: <true|false>

## Abstract

<abstract text, verbatim, no truncation>

## Equations

### From "<section heading>" (p. <N>)

$$<LaTeX>$$
*Equation (<label>)* — <≤25-word context line>

$$<LaTeX>$$
*Equation (<label>)* — <context>

### From "<next section heading>" (p. <N>)

…
```

Consecutive equations sharing a section go under one `### From …` header. Don't repeat the header.

If `--formula-enrichment false`: replace the `$$…$$` block with a fenced code block (no language tag) wrapping the raw text. Prevents markdown renderers from interpreting Unicode soup as math:

````markdown
```
V π H ( x ) = E π [ ∑ H t =1 r t | x 1 = x ]
```
*Equation (1)* — context line
````

## Implementation sketch

```python
from pathlib import Path
from datetime import datetime, timezone
import re

def write_technical_summary(
    out_dir: Path,
    packet: dict,            # already-loaded context-packet.json
    manifest: dict,          # already-loaded run-manifest.json
    enrichment_on: bool,     # from cli_flags
) -> Path:
    """Write technical-summary.md to OUT_DIR. Returns the path."""
    summary_path = out_dir / "technical-summary.md"
    parts = []

    # Header
    profile = packet.get("paper_profile", {})
    title = profile.get("title") or "(title not detected)"
    authors = profile.get("authors") or []
    author_str = ", ".join(authors) if authors else "unknown"
    sha = manifest.get("input_pdf_sha256", "")[:12]
    timestamp = datetime.now(timezone.utc).isoformat()

    parts.append(f"# Technical summary — {title}\n")
    parts.append(f"Authors: {author_str}")
    parts.append(f"Source: {manifest.get('input_path', '')} (SHA {sha})")
    parts.append(f"Generated: {timestamp}")
    parts.append(f"Formula enrichment: {str(enrichment_on).lower()}\n")

    # Abstract
    abstract = _find_abstract(packet)
    if abstract:
        parts.append("## Abstract\n")
        parts.append(abstract)
        parts.append("")  # blank line

    # Equations
    parts.append("## Equations\n")
    equations = packet.get("equations", [])
    if not equations:
        parts.append("_No equations detected in this document._\n")
    else:
        parts.extend(_render_equation_groups(equations, packet, enrichment_on))

    summary_path.write_text("\n".join(parts), encoding="utf-8")
    return summary_path


def _find_abstract(packet: dict) -> str | None:
    """Return the abstract text or None."""
    # Preferred: a section block tagged as abstract.
    for section in packet.get("sections", []):
        if section.get("label") == "abstract":
            return section.get("text", "").strip() or None
    # Fallback: prose blocks between title and first section_header.
    # Stage 02 should expose these as packet["title_to_first_section_prose"]
    # if Docling didn't label an abstract.
    prose_blocks = packet.get("title_to_first_section_prose", [])
    if prose_blocks:
        text = "\n\n".join(b.strip() for b in prose_blocks if b.strip())
        return text or None
    return None


def _render_equation_groups(equations, packet, enrichment_on):
    """Return the equation section content as a list of markdown chunks."""
    out = []
    prev_section_id = None

    sections_by_id = {s["id"]: s for s in packet.get("sections", [])}

    for i, eq in enumerate(equations, start=1):
        section_id = eq.get("section_id")
        page = eq["page"]

        # Group header (only when section changes)
        if section_id != prev_section_id:
            section = sections_by_id.get(section_id, {})
            heading = section.get("heading") or "(unsectioned)"
            out.append("")
            out.append(f"### From \"{heading}\" (p. {page})\n")
            prev_section_id = section_id

        # Equation block
        if enrichment_on:
            latex = eq.get("latex", "").strip()
            out.append(f"$$\n{latex}\n$$")
        else:
            raw = eq.get("text") or eq.get("latex", "")
            out.append("```")
            out.append(raw.strip())
            out.append("```")

        # Label + context line
        label = eq.get("number") or str(i)
        context = _extract_context(eq)
        if context:
            out.append(f"*Equation ({label})* — {context}\n")
        else:
            out.append(f"*Equation ({label})*\n")

    return out


def _extract_context(eq: dict) -> str | None:
    """Up to 25-word hint from the prose preceding this equation."""
    prose = eq.get("preceding_prose", "")
    if not prose:
        return None
    sentences = [s.strip() for s in re.split(r"[.!?]+", prose) if s.strip()]
    if not sentences:
        return None
    last = sentences[-1]
    words = last.split()
    if len(words) > 25:
        last = " ".join(words[:25]) + "…"
    return last
```

## What Stage 02 needs to provide

The implementation above assumes each equation entry in `visuals/equations/equations.json` has two fields the spec hasn't required yet:

- **`section_id`** — the ID of the enclosing section, e.g. `"sec-003"`. Determined by the most recent `section_header` block preceding the formula in Docling document order.
- **`preceding_prose`** — the text of the prose block (`text` or `paragraph` label) immediately preceding the formula in document order. Used for the context line. Empty string if none.

Adding these to Stage 02's equation extractor is small — two extra fields, computed during the same AST walk that produces `latex`, `bbox`, and `image_path`. The schema gains:

```json
{
  "id": "eq-001",
  "page": 2,
  "bbox": [...],
  "latex": "...",
  "image_path": "visuals/equations/equation_001.png",
  "number": "(1)",
  "section_id": "sec-003",      ← new
  "preceding_prose": "..."      ← new
}
```

If Stage 02 doesn't track these, the technical summary falls back gracefully: no `section_id` → equations grouped under `(unsectioned)`; no `preceding_prose` → context line omitted.

## Edge cases

**No equations detected.** Emit the abstract + this single line under `## Equations`:

```markdown
_No equations detected in this document._
```

**No abstract detected.** Omit the `## Abstract` section entirely. Add `abstract_not_found` to `quality-report.json`'s warnings. Don't synthesize.

**Authors unknown.** Render `Authors: unknown`. Don't infer from page 1.

**Title not detected.** Render `# Technical summary — (title not detected)`.

**Numbered label missing.** If `eq.number` is null, use the sequential index across the document. First unnumbered equation → `*Equation (1)*`, second → `*Equation (2)*`. Don't try to interleave with paper-defined labels — sequential is simpler.

**Section heading missing.** Group under `(unsectioned)`. Happens when equations appear before any `section_header` block.

**Multi-line LaTeX in a single equation.** Emit verbatim. The `$$…$$` wrapper accepts multi-line content. Don't normalize whitespace.

## Quality report additions

Two new gates:

```json
"technical_summary_exists": true,
"technical_summary_has_equations": true
```

- `technical_summary_exists` — file is non-empty
- `technical_summary_has_equations` — file contains at least one `$$…$$` block (enrichment-on) or fenced code block under `## Equations` (enrichment-off)

The second being `false` isn't necessarily a failure — some papers have no equations. The report distinguishes "ran and found none" from "didn't run."

One new count:

```json
"counts": {
  ...
  "equations_in_technical_summary": <N>
}
```

This should match `visuals/equations/equations.json`'s entry count. If they diverge, something silently failed — surface as a warning.

## MANIFEST.md additions

In `### Deliverables`, between `paper.md` and `context-packet.json`:

```markdown
- **`technical-summary.md`** — abstract + every equation, grouped by section.
  For math-focused chats: equation translation, derivation checks, code
  generation. Smaller than `paper.md`, faster to paste.
```

In `## What was done to your paper`:

```markdown
- Equations in technical summary: <N>
```

If `N == 0`, append ` — no equations found in this document`.

## What this enhancement does NOT add

- A flag to disable production (always produced; cheap)
- Equation cross-references or hyperlinks (plain markdown only)
- Figure or table inclusion (scoped to abstract + equations specifically)
- A separate equation index or table-of-equations (the section-grouped structure is the index)
- LLM-generated explanations or annotations (this tool doesn't call LLMs)
