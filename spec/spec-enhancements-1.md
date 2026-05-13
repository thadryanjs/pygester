#Two cleanup issues in the same area, please tackle both:
1. Extractors are writing empty stubs, not extracting. On the Foffano enrichment-on run, debug/{figures,tables,references,equations}/*.json are all exactly 2 bytes — literally []. But:

paper.md has 30 $ characters of LaTeX → Docling found equations, but debug/equations/equations.json is empty.
Foffano has 4 figures (Fig. 1, Fig. 2, Fig. 3, Fig. 4) → debug/figures/figures.json is empty.
Foffano has 33 references → debug/references/references.json is empty.
debug/tables/tables.json being empty is actually correct (Foffano has no <table>-shaped tables).

The Docling output has this data — it's in debug/parser/raw_output.json as formula, picture, and bibliography blocks. Stage 02 needs to walk that AST and populate each artifact JSON per the spec's §6.4–§6.8 schemas. Right now the stage is writing [] and exiting.
While you're in there: equations and figures should also get cropped PNGs (debug/equations/equation_NNN.png, debug/figures/figure_NNN.png) — bbox + page raster + PIL crop. These are the visual fallback for when extracted LaTeX is garbled.
2. Don't write empty files or their parent directories. If an extractor finds zero items, don't create debug/<thing>/<thing>.json at all. Don't create the directory either. Empty 2-byte JSONs in nested directories is noise; the absence of the directory communicates "zero found" cleanly. Record the count (including zero) in quality-report.json where it belongs — that's the right place to convey "we ran and found nothing."
Verification after both changes:
bashpixi run test-foffano-enrichment-on
ls runs/foffano-fe-on/debug/                              # should NOT show empty tables/ dir
ls runs/foffano-fe-on/debug/equations/                    # should have equations.json + PNGs
ls runs/foffano-fe-on/debug/figures/                      # should have figures.json + PNGs
wc -l runs/foffano-fe-on/debug/equations/equations.json   # >> 1 line, real entries
cat runs/foffano-fe-on/quality-report.json | grep -i count   # zero-counts should appear here
Spec section §6 has the target schemas. Quality report should grow per-extractor counts (equations_found, figures_found, tables_found, references_found). spec-enhancements-1.md

Implementation details for `technical-summary.md` that aren't in `spec.md`. The spec covers the what; this covers the how and the edge cases.

## Generation order within Stage 03

1. `context-packet.json` (others reference its data)
2. `technical-summary.md` (uses packet's section + equation arrays)
3. `quality-report.json` (uses all of the above to populate gates)
4. `MANIFEST.md` (uses everything; written last)

All four are derived from the same inputs (`debug/text/`, `debug/equations/`, `debug/text/sections.json`). The implementing module should load those once and pass them to each writer.

## Edge cases the spec doesn't cover

**No equations detected.** Emit the abstract section and a single line under `## Equations`:

```markdown
_No equations detected in this document._
```

**No abstract detected.** Omit the `## Abstract` section entirely. Add `abstract_not_found` to `quality-report.json` anomalies. Don't try to synthesize one.

**Authors unknown.** If `paper_profile.authors` is null or empty, render as `Authors: unknown`. Don't infer from the first page.

**Equation context extraction fails.** If the prose block immediately preceding a formula is missing, empty, or doesn't split into sentences, omit the `— …` portion. The `*Equation (N)*` line stands alone with no trailing context.

**Equation labels missing.** If Docling didn't capture a numbered label like `(1)`, number sequentially starting at 1 across the document (not per-section).

## Equation rendering by enrichment mode

**With `--formula-enrichment on`:** wrap LaTeX in `$$…$$` on its own line. Markdown renderers with KaTeX/MathJax will display it as math; plaintext renderers show the LaTeX source.

**With `--formula-enrichment off`:** wrap the raw text (flattened Unicode) in a fenced code block with no language tag:

````
```
V π H ( x ) = E π [ ∑ H t =1 r t | x 1 = x ]
```
````

The fence prevents any renderer from trying to interpret the Unicode as math syntax.

## Context line extraction algorithm

For each formula block in Docling document order:

1. Walk backward through Docling's block list to find the most recent prose block (`text`, `paragraph`).
2. If found, take its `text` field. Split on `.`, `?`, `!` (sentence terminators). Take the last non-empty sentence.
3. Cap at 25 words. If longer, truncate at word boundary and append `…`.
4. If step 1 returns nothing or step 2 yields empty text, omit the context line.

Best-effort. A 5% failure rate on tricky papers is fine — the equation is still there.

## Section grouping

Section membership: the most recent `section_header` block preceding the formula in document order.

Consecutive equations sharing a section go under the same `### From "<heading>" (p. <N>)` header. Don't repeat the header.

The page number `<N>` is the formula's page, not the section header's page. (A section can span multiple pages; the equation's page is what the user needs to verify against the PNG.)

## Quality report additions

Two new gates in `quality-report.json`:

- `technical_summary_exists` — `technical-summary.md` is non-empty
- `technical_summary_has_equations` — file contains at least one rendered equation block

The second gate being false isn't necessarily a failure — some papers have no equations. The report distinguishes "ran and found none" from "didn't run."

## MANIFEST.md additions

In `## What was done to your paper`, add:

```markdown
- Equations detected: <N> (in `technical-summary.md`)
```

If `N == 0`, append `— no equations found in this document`.

## What this enhancement does NOT add

- A flag to disable production (always produced; cheap)
- Equation cross-references or hyperlinks (plain markdown only)
- Figure or table inclusion (scoped to abstract + equations specifically)
- A separate equation index or table-of-equations (the section-grouped structure is the index)
