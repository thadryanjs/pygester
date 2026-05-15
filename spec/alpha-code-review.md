# alpha-code-review.md

Alpha readiness review. Check code, specs, README, scripts, and sample runs for mismatch, stale paths, dead files, broken outputs. Not polish.

**Audience:** coding agent. Open files. Don't guess. If code and spec disagree, mark `QUESTION` unless decision is clearly stale.

**Status labels:**

- `OK` — checked, no alpha issue
- `FIX: <what>` — must change before alpha
- `DEFER: <why>` — real issue, not a blocker
- `QUESTION: <disparity>` — code/spec disagreement, may be intentional

**Rules:**

- Prefer documenting intentional behavior over forcing code to old spec.
- Do not delete sample runs without owner approval.
- Do not run long Docling jobs unless owner asks.
- Canonical CLI flag values: `true`/`false`.
- Canonical output layout: `paper.md`, `context-packet.json`, `quality-report.json`, `MANIFEST.md`, `pages/`, `visuals/`, `tables/`, `references/`, `debug/`.

---

## 0. Orient

Read first: `src/process-pdf.py`, `src/01-parse.py`, `src/02-clean.py`, `src/03-packet.py`, `src/common.py`, `spec/spec.md`, `readme.md`, `pixi.toml`.

Cheap scans:

```bash
find src -type d -name __pycache__
grep -R "_01_parse\|generate_summary\|consolidate_text\|context_packet\|quality_report\|artifacts/\|outputs/\|--cache\|--fail-on-low-quality\|enrichment on\|enrichment off" -n . --include='*.py' --include='*.md' --include='*.toml' --include='*.sh'
```

---

## 1. File hygiene

- `src/parsers/mineru_parser.py` — exists and only raises unsupported. `FIX: delete` (and update any spec/README mentions).
- `src/__pycache__/` and `src/parsers/__pycache__/` — stale entries from renamed files. `FIX: rm -rf`. Confirm `.gitignore` excludes.
- `tests/` — old `artifacts/`/`outputs/` layout, `translation.md`, etc. `QUESTION: keep as historical or remove?`
- `runs/foffano-run/`, `runs/cortes-run/` — old layout (`debug/equations/eq-001.png` not `visuals/equations/equation_001.png`). `QUESTION: regenerate, mark historical, or move?`
- `runs/test-fe-on/` — partial. Likely `FIX: delete`.
- `qc-enrichment.sh` exists in both `src/` and `scripts/`; pixi `qc` task points at `src/`. `FIX: delete duplicate`.

---

## 2. Stage 01 — `src/01-parse.py` + `src/parsers/docling_parser.py`

**CLI flags accepted:** positional `pdf`, `--out`, `--formula-enrichment`, `--code-enrichment`, `--ocr`, `--max-pages`, `--dpi`. Do **not** accept `--cache` or `--fail-on-low-quality` unless code re-adds them.

**Known findings:**

- README mentions `--cache` and `--fail-on-low-quality`; code doesn't. `FIX: update README`.
- `_flag_on()` treats only string `"true"` as enabled. Confirm.
- `--max-pages` soft-truncates markdown + limits raster page count; raw JSON may still contain full document. `QUESTION: intentional?`
- `--code-enrichment` recorded but not implemented as a Docling pipeline option. `QUESTION: implement, document gap, or drop flag?`
- `parser_name` parameter in `parse_pdf()` is unused. `FIX: remove`.

**Outputs to verify exist:** `debug/original.pdf`, `debug/parser/raw_output.{json,md}`, `pages/page_NNNN.png`, `debug/run-manifest.json`. Manifest fields: schema/tool version, timestamp, input path + SHA256, flags, parser name/version/config, page count, stages completed.

---

## 3. Stage 02 — `src/02-clean.py`

### paper.md and intermediates

- Built from `debug/parser/raw_output.md` (post-process, not rebuild). Confirm.
- Writes `debug/intermediate/markdown/01-with-frontmatter.md` then top-level `paper.md`.
- Writes `debug/intermediate/text/{plaintext.txt, sections.json, provenance.json}`.

**Known findings:**

- `add_frontmatter()` computes `formula = ...` but never uses it; also checks `"on"` despite canonical `true/false`. `FIX: remove dead var, fix flag check`.
- `provenance.json` currently `[]`. `QUESTION: placeholder or bug?`

### Extractors (equations / figures / tables / code / references)

Common pattern: read Docling JSON, build entries with `id/page/bbox/content/image_path`, crop PNG, write sidecar JSON. Sidecars: `visuals/equations/`, `visuals/figures/`, `visuals/code/`, top-level `tables/`, `references/`.

**Don't create dirs or sidecar JSONs for zero-item types.** Currently many extractors create dirs unconditionally. `FIX: gate dir/file creation on count > 0`.

**Specific findings:**

- Equations: function creates `visuals/equations/` before knowing count. Past bug had formulas in Docling AST but extractor returned empty — verify current Docling JSON shape. Crops use `_bbox_to_pixels()` — verify `coord_origin` handling.
- Figures: stale local `image_path = f"debug/figures/..."` shadowed by entry's correct `visuals/figures/...`. `FIX: remove dead var`.
- Tables: creates `debug/tables/` unconditionally; doesn't write CSVs despite `csv_path` values. `QUESTION: CSV expected by spec or dropped?`
- Code: extraction runs regardless of `--code-enrichment` flag; creates `visuals/code/` unconditionally. `FIX or QUESTION` per owner intent.
- References: creates `debug/references/` after finding refs but never writes there. May miss Docling `bibliography` blocks (Foffano-era bug).

### Quality report

`canonical_non_empty`, `paper_md_exists`, `context_packet_valid` are hardcoded `True`. **Alpha blocker.** `FIX: implement real existence + non-empty checks; do not assert context-packet validity in Stage 02 since it isn't built yet.` Should also warn when count > 0 but sidecar/crops missing.

---

## 4. Stage 03 — `src/03-packet.py`

**Reads:** `debug/run-manifest.json`, `quality-report.json`, `debug/intermediate/text/sections.json`, `visuals/{equations,figures,code}/*.json`, `tables/tables.json`, `references/references.json`.

**Writes:** `context-packet.json`, `quality-report.json` (refresh), `MANIFEST.md`, optionally `technical-summary.md`.

**Known findings:**

- `technical-summary.md` not currently written. `QUESTION: implement (per spec-enhancements-1.md), defer, or drop from alpha scope?`
- `MANIFEST.md` uses `Math is {math_status} depending on whether formula enrichment was on.` — awkward conditional, may still use `on/off` language. `FIX: pick one branch cleanly`:
  - true: `Math is LaTeX where Docling extracted formulas.`
  - false: `Math is flattened Unicode from Docling.`
- Verify reproduce-command in MANIFEST includes all relevant flags (including `--dpi`, `--max-pages` if set).
- `quality-report.json` should be refreshed by Stage 03 if Stage 02 hardcoded any fields.

---

## 5. Wrapper — `src/process-pdf.py`

- Accepts and passes: `pdf`, `--out`, `--formula-enrichment`, `--code-enrichment`, `--ocr`, `--max-pages`, `--dpi`. Does **not** advertise `--cache` or `--fail-on-low-quality`.
- Runs Stage 01 → 02 → 03 via `subprocess.run(..., check=True)`. Exit codes propagate.
- Skip behavior: skips Stage 01 if `debug/parser/raw_output.json` exists, Stage 02 if `paper.md` exists, Stage 03 if `context-packet.json` exists.

**Known finding:** skip behavior can reuse outputs across different flag values. `QUESTION: document as prototype behavior (use clean --out for fresh flags) or invalidate when flags differ?`

---

## 6. Cross-cutting

**Logging:** `setup_logging()` writes to stdout + appends to `debug/run.log`. Each stage logs start/end. Noisy libraries (`docling`, `transformers`, `huggingface_hub`) suppressed.

**Flag values everywhere:**

```bash
grep -R "enrichment on\|enrichment off\|ocr on\|ocr off" -n . --include='*.sh' --include='*.md' --include='*.py'
```

All runnable scripts use `true/false`. Spec enhancement docs may still have `on/off`. `FIX: update`.

**Dead code:**

- `src/common.py`: `shutil` import unused. `FIX: remove`.
- `src/02-clean.py`: `datetime`, `timezone` imports unused; stale local vars. `FIX: remove`.
- `src/parsers/base.py`: `Parser` Protocol not consumed by type annotations. `DEFER` if owner wants future abstraction, else `FIX: drop`.

**Naming consistency:** kebab-case top-level (`context-packet.json`, `quality-report.json`, `run-manifest.json`), underscore inside `debug/parser/` (`raw_output.json`). Verify in README, spec, scripts.

---

## 7. Pixi / scripts / Slurm

- **`pixi.toml`:** every task points at a real script. No references to deleted files. `test-texify` is experimental. `clean` not aggressive (`QUESTION`).
- **`scripts/run-*.sh`:** each calls `src/process-pdf.py` with correct asset path, `--out` matching script name, `--formula-enrichment true/false` matching `-fe-on`/`-fe-off`. No unsupported flags.
- **`slurm/*.sh`:** 8 scripts (foffano/cortes/mishmast/nikishin × on/off). Each calls matching `scripts/run-*.sh`. Resource requests sane.

---

## 8. Spec accuracy

- **`spec/spec.md`:** CLI flags, output tree, stage responsibilities, exit codes, `max-pages` behavior, code-enrichment claims, OCR behavior, quality gates — all match code or marked planned.
- **`spec-enhancements-1.md`** (technical-summary.md): implementation matches or marked deferred.
- **`spec-enhancements-2.md`** (logging): implemented ad-hoc; merge into spec or mark done.
- **`spec-enhancements-3.md`** (crops): paths use `visuals/...` not `debug/equations/`.
- **README:** quickstart works. Output paths use current layout. Names use hyphens. No unsupported flags. No claims of features not in code (header stripping, section sanity pass, abstract synthesis, auto-OCR).

**Known finding:** README mentions old `outputs/`, `artifacts/`, `context_packet.json`, `quality_report.json`, `--cache`, `--fail-on-low-quality`, auto-OCR, and cleanup behavior not in code. `FIX`.

---

## 9. Non-goals (document somewhere visible)

- Native-text PDFs are target. No auto-OCR.
- No specialist fallback for broken formula extraction.
- No batch mode.
- No LLM/API calls.
- Equation extraction quality observed across 4 papers ≈ 85-90% clean.
- Prototype: not packaged, no semver, output schema may change.
- Resume behavior reuses existing stage outputs; use clean `--out` for fresh flags.

Unhomed non-goals: `FIX: add to README or ALPHA_RELEASE_NOTES.md`.

---

## 10. Deferred work (file, don't implement)

Confirm in `TODO.md` or `admin/todo.md`:

richer quality-report schema, auto-detect OCR, Texify sidecar, per-equation progress logging, batch mode, picture description, true parser-side `max_pages`, code-enrichment implementation.

---

## 11. Optional fresh-run validation

Only with owner approval (long run).

```bash
rm -rf runs/alpha-foffano-fe-on
pixi run python src/process-pdf.py \
  'assets/Foffano et al. - 2023 - Conformal Off-Policy Evaluation in Markov Decision Processes.pdf' \
  --out runs/alpha-foffano-fe-on \
  --formula-enrichment true --code-enrichment false --ocr false --dpi 200
```

Check: deliverables non-empty, page PNGs match page count, `visuals/equations/equations.json` populated, crops exist, `references/references.json` non-empty, no empty `tables/` if no tables, quality report reflects reality.

---

## Reporting

```markdown
# Alpha code review report

## Summary
- Status: NOT READY / READY WITH DEFERS / READY
- Blockers: <short list>
- Owner questions: <short list>

## Findings by section
1. File hygiene
2. Stage 01
3. Stage 02
4. Stage 03
5. Wrapper
6. Cross-cutting
7. Pixi/scripts/slurm
8. Specs/README
9. Non-goals
10. Deferred work
11. Fresh-run validation: skipped / passed / failed

## Owner questions
1. ...
```

Skip OK. Give file paths and exact mismatches for FIX/QUESTION.

---

## Alpha acceptance

- No unresolved `FIX` in sections 1–8.
- All `QUESTION` answered → `OK`, `FIX`, or `DEFER`.
- Non-goals documented visibly.
- Deferred work filed.
- README quickstart matches code.
- Fresh Foffano run produces complete bundle without intervention (or owner waives).

---

## Review findings (2026-05-15, pre-alpha)

> Conducted by separate model against the above spec. All items verified by reading source, not guessing.

### Blockers

- **`--code-enrichment` missing from `process-pdf.py` and `01-parse.py` argparse.** Every `scripts/run-*.sh` and every slurm job passes `--code-enrichment false` → subprocess crash. Fix: add arg to both argparse blocks; pass through to `DoclingParser` (even as no-op).

### FIX (must resolve before alpha)

- `src/parsers/mineru_parser.py` — only raises `NotImplementedError`. Delete.
- `src/__pycache__/` and `src/parsers/__pycache__/` — stale `.pyc` from deleted scripts (`consolidate_text`, `generate_summary`, `generate_translation`, `normalize`, `section_sanity`, `_01_parse`, etc.). `rm -rf` both. Add `**/__pycache__/` and `**/*.pyc` to `.gitignore`.
- `scripts/qc-enrichment.sh` — duplicates `src/qc-enrichment.sh` and has a bash/Python f-string bug (`$failures` unquoted). Delete `scripts/` copy; `pixi qc` already points at `src/`.
- `common.py`: `shutil` imported, never used. Remove.
- `02-clean.py` figures extractor: dead `image_path = None` assignment before the try block (immediately overwritten in fig_entry). Remove.
- `MANIFEST.md` template in `03-packet.py`: `Math is {math_status} depending on whether formula enrichment was on.` renders awkwardly with the variable filled in. Pick one branch: `"Math is LaTeX."` or `"Math is Unicode (formula enrichment was off)."` — not both joined.
- `MANIFEST.md` reproduce command missing `--dpi` and `--max-pages` (conditional on non-default). Add both.
- Stage 03 logs `"Wrote quality-report.json"` but Stage 02 owns that file. Change to `"Quality report written by Stage 02"` or drop the line.
- `README.md`: `"Math kept as LaTeX"` stated unconditionally. Qualify: only true with `--formula-enrichment true`.
- `README.md` pipeline diagram references `normalize →` step — that script is deleted. Update diagram.
- `runs/test-fe-on/` — partial run, no deliverables. Delete.

### QUESTION (owner decision required)

1. **`--code-enrichment` intent**: add to argparse as accepted-but-ignored, or drop from all run scripts entirely?
2. **`runs/foffano-run/`** (old layout: `debug/equations/eq-001.png`, stale quality-report gates) and **`runs/cortes-run/`** (partial, no deliverables): mark historical, delete, or regenerate with current code?
3. **`tests/`** directory: old `artifacts/`/`outputs/` layout, stale `translation.md`. Keep as historical or remove?
4. **`pixi clean` task**: `rm -rf run run-foffano run-cortes runs` nukes all of `runs/` including slurm outputs. Intentional?
5. **`--max-pages` and raw JSON**: flag caps raster + markdown but Docling parses the full doc. Intentional? Document either way.
6. **Skip-on-existing behavior** in `process-pdf.py`: reuses Stage outputs even if flags changed. Document as "use clean `--out` for fresh flags" in README or add a warning.

### DEFER (real issues, not alpha blockers)

- `src/parsers/base.py`: `Parser` Protocol not used by any type annotation. Drop or keep for future swap.
- `spec-enhancements-1/2/3.md` use `on/off` flag language; code uses `true/false`. Spec docs only — no runtime impact.
- `process-pdf.py` uses `print()` for stage-transition messages instead of `setup_logging`. Wrapper messages appear on stdout but not in `debug/run.log`.
- `02-clean.py`: explicit `import logging` at top is redundant (pulled in via `setup_logging` from `common`). Harmless.
- Code extractor runs regardless of `--code-enrichment` flag. Crops are always useful. Document as always-on behavior in spec.
- `context-packet.json` `paper_profile.title` hardcoded `"Unknown"`. Document: Docling doesn't expose title at this abstraction level.
- `admin/todo.md` references old paths (`artifacts/`, `outputs/`, `context_packet.json`). Stale notes, not user-facing.

### Verified OK

- Stage 01 outputs all present and correct per spec.
- `_flag_on()` correctly treats only `"true"` as enabled.
- Extractor gating: sidecars and dirs only created when count > 0.
- `_bbox_to_pixels()` handles `BOTTOMLEFT`/`TOPLEFT`, padding, clamping correctly.
- `write_quality_report()` uses real existence checks — no hardcoded `True`.
- `setup_logging()` correct: stdout + append to `debug/run.log`, noisy libs suppressed.
- All slurm scripts call correct `scripts/run-*.sh` counterparts.
- `pixi qc` task points at correct (`src/`) qc script.
- README: no `--cache`, no `--fail-on-low-quality`, no auto-OCR claims, correct output paths.
- `spec.md` output tree, stage responsibilities, quality gates match code.
