
import sys
from importlib.metadata import PackageNotFoundError, version

from pathlib import Path
from typing import Any

from .base import ParserOutput


class DoclingParser:
    name = "docling"

    def __init__(self) -> None:
        try:
            self.version = version("docling")
        except PackageNotFoundError:
            self.version = "unknown"

    def parse(
        self,
        pdf_path: Path,
        max_pages: int | None = None,
        do_formula_enrichment: bool = True,
        do_code_enrichment: bool = False,
        do_ocr: bool = False,
    ) -> ParserOutput:
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Docling not installed. Run `uv sync` then retry."
            ) from exc

        pipeline_options = PdfPipelineOptions()
        if sys.platform == "darwin":
            pipeline_options.device = "cpu"
        pipeline_options.do_ocr = do_ocr
        pipeline_options.do_formula_enrichment = do_formula_enrichment
        # Note: Docling doesn't have do_code_enrichment; table_structure defaults to True
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(str(pdf_path))
        document = result.document

        markdown = ""
        if hasattr(document, "export_to_markdown"):
            markdown = document.export_to_markdown() or ""

        raw_output: dict[str, Any] = {}
        if hasattr(document, "export_to_dict"):
            raw_output = document.export_to_dict() or {}

        page_count = None
        if isinstance(raw_output, dict):
            pages = raw_output.get("pages")
            if isinstance(pages, list):
                page_count = len(pages)

        if max_pages is not None and markdown:
            # Soft cap fallback. True parser-side page limiting can be added later.
            markdown = "\n".join(markdown.splitlines()[: max_pages * 200])

        return ParserOutput(markdown=markdown, raw_output=raw_output, page_count=page_count)
