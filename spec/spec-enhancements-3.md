# spec-enhancements-3.md

Add per-block PNG crops for equations, figures, and code blocks. Each block in `raw_output.json` has a bbox; use it to crop the corresponding page raster and save the result alongside the structured artifact JSON.

Goal: when LaTeX from formula enrichment is malformed or you want to verify an LLM's interpretation of a figure, the visual ground truth is one image lookup away.

## Where this lives

Stage 02. After walking Docling's AST to populate `debug/equations/equations.json` etc. (the bug from the previous cleanup pass), the same loop also writes the crop alongside.

```
debug/
├── equations/
│   ├── equations.json
│   ├── equation_001.png
│   ├── equation_002.png
│   └── ...
├── figures/
│   ├── figures.json
│   ├── figure_001.png
│   └── ...
└── code/                  # only if --code-enrichment on
    ├── code.json
    ├── code_001.png
    └── ...
```

Numbering: sequential across the document, 3-digit zero-padded. Independent per artifact type (equations and figures both start at 001).

## The crop operation

```python
from PIL import Image
from pathlib import Path

def crop_block(page_png: Path, bbox: dict, dpi: int, padding_px: int = 6) -> Image.Image:
    """Crop a Docling block from a page raster.

    bbox is Docling's prov[0]['bbox'] dict with l, t, r, b, coord_origin.
    dpi is the rasterization DPI from CLI flags (default 200).
    padding_px adds breathing room so subscripts/superscripts don't get clipped.
    """
    page = Image.open(page_png)
    page_h_px = page.height

    scale = dpi / 72.0  # PDF points → pixels

    x0 = bbox["l"] * scale
    x1 = bbox["r"] * scale

    if bbox.get("coord_origin", "BOTTOMLEFT") == "BOTTOMLEFT":
        # Flip Y axis: PDF measures from bottom, images from top
        y0 = page_h_px - (bbox["t"] * scale)
        y1 = page_h_px - (bbox["b"] * scale)
    else:
        # TOPLEFT origin: same coordinate system as image
        y0 = bbox["t"] * scale
        y1 = bbox["b"] * scale

    # Normalize (top < bottom, left < right) after flip
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))

    # Apply padding, clamped to page bounds
    x0 = max(0, x0 - padding_px)
    y0 = max(0, y0 - padding_px)
    x1 = min(page.width, x1 + padding_px)
    y1 = min(page_h_px, y1 + padding_px)

    return page.crop((x0, y0, x1, y1))
```

## Per-artifact loop

In whatever Stage 02 function walks the AST and writes `equations.json`:

```python
equations_dir = out_dir / "debug" / "equations"
equations_dir.mkdir(parents=True, exist_ok=True)

equations = []
for i, block in enumerate(formula_blocks, start=1):
    prov = block["prov"][0]
    page_num = prov["page_no"]
    bbox = prov["bbox"]

    page_png = out_dir / "pages" / f"page_{page_num:04d}.png"
    crop = crop_block(page_png, bbox, dpi=cli_flags["dpi"])

    crop_filename = f"equation_{i:03d}.png"
    crop.save(equations_dir / crop_filename)

    equations.append({
        "id": f"eq-{i:03d}",
        "page": page_num,
        "bbox": bbox,
        "latex": block.get("text", ""),
        "image_path": f"debug/equations/{crop_filename}",
        "number": _extract_equation_number(block),  # e.g., "(11)" or None
    })

write_json(equations_dir / "equations.json", equations)
```

Same pattern for figures (block label `picture`) and code (block label `code`).

## Schema additions

`equations.json` entries gain `image_path` (relative to OUT_DIR). Same for `figures.json` and `code.json`. The path lets a downstream consumer (the technical-summary.md writer, an LLM client, etc.) load the crop without recomputing it from bbox.

`context-packet.json`'s equations/figures/code arrays inherit `image_path` from the same source.

## Coordinate-origin gotcha

Docling's bbox `coord_origin` field is the load-bearing detail. PDFs traditionally measure from bottom-left; images measure from top-left. If you skip the flip, your crops will land in the wrong place vertically.

Verification: after the first run, open `debug/equations/equation_001.png` and confirm it actually shows equation (1). If you got a chunk of header or page-number area, the flip is wrong — invert the condition in `crop_block`.

Docling may also occasionally report bboxes in `TOPLEFT` origin (e.g., for some block types or in newer versions). The function above handles both cases by branching on `coord_origin`.

## Padding

6 pixels at 200 DPI ≈ 0.03 inches ≈ 2-3 character widths. Enough to avoid clipping subscripts/superscripts that sit just outside the detected bbox, not enough to grab neighboring lines. If equations come out clipped, raise to 10. If they pick up surrounding text, drop to 3.

## Always produced

Crops are not gated by enrichment flags. Even with `--formula-enrichment off`, you still have bboxes (from the layout model, which always runs). The crops are useful in their own right — they're the visual ground truth regardless of whether you have LaTeX.

This means a fast enrichment-off run produces a complete bundle of cropped equations in seconds, even if their LaTeX is Unicode soup. That's a useful workflow: triage mode gives you visual fallback without paying for enrichment.

## Filename stability

`equation_001.png` corresponds to the first formula block in Docling document order. Same paper, same parser version, same DPI → same numbering across runs. This is important for the `image_path` references in `equations.json` and `context-packet.json` to stay valid.

If equation numbering in the paper itself (e.g., "(11)" in the rendered text) doesn't match the sequential filename order, that's fine — the `number` field in the JSON entry records the paper's label, while the filename records document order. Both are useful for different lookups.

## Logging

Per the logging enhancement (spec-enhancements-2.md), Stage 02 should log:

```
[hh:mm:ss] Cropping 30 equations, 4 figures
[hh:mm:ss] Crops written (Xs)
```

Don't log per-crop — that's noise at this scale. The aggregate count and timing is enough.

## Quality report additions

Add to the counts section:

- `equation_crops_written`: N
- `figure_crops_written`: N
- `code_crops_written`: N (zero unless `--code-enrichment on`)

These should match the corresponding entry counts in `equations.json` etc. If they diverge, something silently failed during cropping — surface it in the quality report's `warnings` field.

## Failure handling

If `crop_block` raises (corrupt bbox, missing page PNG, PIL error on a degenerate region), don't kill the stage. Log a warning, skip the crop, leave the JSON entry without `image_path`, increment a `crop_failures` counter in the quality report.

```python
try:
    crop = crop_block(page_png, bbox, dpi=cli_flags["dpi"])
    crop.save(equations_dir / crop_filename)
    image_path = f"debug/equations/{crop_filename}"
except Exception as e:
    log.warning(f"Crop failed for equation {i}: {e}")
    image_path = None
```

The equation still appears in `equations.json`, just without a visual. The pipeline continues.

## What this enhancement does NOT add

- Vector extraction from PDF (using embedded image objects directly). Rasterized crops at 200 DPI are sufficient for human and LLM verification.
- OCR of the cropped images. The LaTeX comes from Docling's formula enrichment; the crop is for verification only.
- Comparison of cropped image vs rendered LaTeX (the "is the LaTeX trustworthy?" check). That's a separate enhancement, downstream of this one — it needs crops to exist before it can run.
- Per-equation specialist fallback (Texify on broken cases). Also downstream — needs crops as input.

## Why this is high-leverage

Both downstream enhancements you might want next — Texify fallback, or LaTeX-vs-image render check — require per-block crops as their input. Implementing this first unlocks both of those without coupling them. It also gives users a workable verification path *today*: open `equation_011.png` next to the LLM's translation, eyeball the comparison. That's the math-spot-check workflow made concrete.
