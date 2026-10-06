"""PDF loader backed by PyMuPDF.

The loader extracts structure only. It never invokes an LLM, OCR engine or
vision model.
"""

from __future__ import annotations

import contextlib
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from l1_data.errors import (
    EmptyPDFError,
    InvalidPDFError,
    NoExtractableTextError,
    PDFBackendUnavailableError,
    PDFNotFoundError,
    PDFReadError,
)
from l1_data.models import BBox, RawDocument, RawImage, RawPage, RawTable, RawTextBlock, TextLine, TextSpan


def _safe_document_id(stem: str) -> str:
    value = re.sub(r"[^\w.-]+", "_", stem, flags=re.UNICODE).strip("._")
    return (value or "document")[:80]


def _bbox(value: Any) -> BBox:
    x0, y0, x1, y1 = (float(item) for item in value)
    return BBox(x0=x0, y0=y0, x1=x1, y1=y1)


@dataclass(slots=True)
class PDFLoader:
    """Load one PDF into a structure-preserving RawDocument."""

    detect_tables: bool = True
    extract_images: bool = True
    max_pages: int | None = None

    def __post_init__(self) -> None:
        if self.max_pages is not None and self.max_pages <= 0:
            raise ValueError("max_pages must be positive when provided")

    def load(self, pdf_path: str | Path) -> RawDocument:
        path = Path(pdf_path).expanduser().resolve()
        self._validate_path(path)

        try:
            import pymupdf
        except ImportError as exc:
            raise PDFBackendUnavailableError() from exc

        try:
            document = pymupdf.open(path)
        except Exception as exc:
            raise PDFReadError(path, str(exc)) from exc

        try:
            if document.needs_pass:
                raise PDFReadError(path, "encrypted PDFs are not supported")
            if document.page_count <= 0:
                raise EmptyPDFError(path)

            document_id = _safe_document_id(path.stem)
            pages: list[RawPage] = []
            page_limit = document.page_count if self.max_pages is None else min(document.page_count, self.max_pages)

            for page_index in range(page_limit):
                page = document.load_page(page_index)
                pages.append(self._load_page(document, page, page_index + 1, document_id))

            has_text = any(
                (isinstance(element, RawTextBlock) and bool(element.text.strip()))
                or (isinstance(element, RawTable) and any(any(cell.strip() for cell in row) for row in element.rows))
                for page in pages
                for element in page.elements
            )
            if not has_text:
                raise NoExtractableTextError(path)

            title = next(
                (
                    element.text.strip()
                    for page in pages
                    for element in page.elements
                    if isinstance(element, RawTextBlock) and element.text.strip()
                ),
                None,
            )
            return RawDocument(
                document_id=document_id,
                source_path=str(path),
                page_count=len(pages),
                pages=tuple(pages),
                title=title,
                metadata={
                    "backend": "pymupdf",
                    "backend_version": getattr(pymupdf, "__version__", "unknown"),
                    "source_total_pages": document.page_count,
                    "truncated": page_limit < document.page_count,
                },
            )
        finally:
            document.close()

    @staticmethod
    def _validate_path(path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise PDFNotFoundError(path)
        if path.suffix.lower() != ".pdf":
            raise InvalidPDFError(path, "file extension must be .pdf")
        try:
            header = path.open("rb").read(5)
        except OSError as exc:
            raise PDFReadError(path, str(exc)) from exc
        if header != b"%PDF-":
            raise InvalidPDFError(path, "missing %PDF- signature")

    def _load_page(self, document: Any, page: Any, page_number: int, document_id: str) -> RawPage:
        page_dict = page.get_text("dict", sort=True)
        table_elements = self._extract_tables(page, page_number, document_id)
        table_boxes = [table.bbox for table in table_elements]
        text_elements: list[RawTextBlock] = []

        for block_index, block in enumerate(page_dict.get("blocks", []), start=1):
            if block.get("type") != 0:
                continue
            block_bbox = _bbox(block.get("bbox", (0, 0, 0, 0)))
            if any(block_bbox.overlap_ratio(table_box) >= 0.35 for table_box in table_boxes):
                continue
            lines = self._extract_lines(block)
            if not lines:
                continue
            text_elements.append(
                RawTextBlock(
                    block_id=f"{document_id}-p{page_number:04d}-b{block_index:03d}",
                    bbox=block_bbox,
                    lines=tuple(lines),
                )
            )

        image_elements = self._extract_images(document, page, page_dict, page_number, document_id)
        elements = tuple(sorted([*text_elements, *table_elements, *image_elements], key=lambda item: (item.bbox.y0, item.bbox.x0)))
        return RawPage(
            page_number=page_number,
            width=float(page.rect.width),
            height=float(page.rect.height),
            elements=elements,
        )

    @staticmethod
    def _extract_lines(block: Any) -> list[TextLine]:
        lines: list[TextLine] = []
        for line in block.get("lines", []):
            spans: list[TextSpan] = []
            for span in line.get("spans", []):
                text = str(span.get("text", ""))
                flags = int(span.get("flags", 0))
                spans.append(
                    TextSpan(
                        text=text,
                        size=float(span.get("size", 0.0)),
                        font=span.get("font"),
                        bold=bool(flags & 16),
                        italic=bool(flags & 2),
                    )
                )
            text = "".join(span.text for span in spans).strip()
            if not text:
                continue
            lines.append(TextLine(text=text, bbox=_bbox(line.get("bbox", block.get("bbox", (0, 0, 0, 0)))), spans=tuple(spans)))
        return lines

    def _extract_tables(self, page: Any, page_number: int, document_id: str) -> list[RawTable]:
        if not self.detect_tables:
            return []
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                finder = page.find_tables()
        except Exception:
            return []

        tables: list[RawTable] = []
        for table_index, table in enumerate(getattr(finder, "tables", ()), start=1):
            try:
                raw_rows = table.extract() or []
            except Exception:
                continue
            rows = tuple(
                tuple("" if cell is None else str(cell).strip() for cell in row)
                for row in raw_rows
            )
            rows = tuple(row for row in rows if any(cell for cell in row))
            if not rows:
                continue
            tables.append(
                RawTable(
                    table_id=f"{document_id}-p{page_number:04d}-t{table_index:03d}",
                    bbox=_bbox(table.bbox),
                    rows=rows,
                )
            )
        return tables

    def _extract_images(
        self,
        document: Any,
        page: Any,
        page_dict: Any,
        page_number: int,
        document_id: str,
    ) -> list[RawImage]:
        image_blocks = [block for block in page_dict.get("blocks", []) if block.get("type") == 1]
        image_refs = list(page.get_images(full=True)) if self.extract_images else []
        count = max(len(image_blocks), len(image_refs)) if self.extract_images else len(image_blocks)
        images: list[RawImage] = []

        for image_index in range(1, count + 1):
            block = image_blocks[image_index - 1] if image_index <= len(image_blocks) else None
            raw_bbox = block.get("bbox") if block else page.rect
            data: bytes | None = None
            extension: str | None = None
            width: int | None = None
            height: int | None = None

            if self.extract_images and image_index <= len(image_refs):
                info = image_refs[image_index - 1]
                width = int(info[2]) if len(info) > 2 else None
                height = int(info[3]) if len(info) > 3 else None
                try:
                    extracted = document.extract_image(int(info[0]))
                    data = extracted.get("image")
                    extension = extracted.get("ext")
                except Exception:
                    data = None
                    extension = None

            figure_id = f"{document_id}-p{page_number:04d}-f{image_index:03d}"
            images.append(
                RawImage(
                    figure_id=figure_id,
                    page_number=page_number,
                    bbox=_bbox(raw_bbox),
                    extension=extension,
                    data=data,
                    width=width,
                    height=height,
                )
            )
        return images