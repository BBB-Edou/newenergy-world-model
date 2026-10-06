"""Convert a structured RawDocument into deterministic Markdown."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

from l1_data.errors import NoExtractableTextError
from l1_data.models import RawDocument, RawImage, RawTable, RawTextBlock


_NUMBERED_HEADING_RE = re.compile(r"^(?P<number>\d+(?:\.\d+){0,5})(?:[.)])?[ \t\u3000]+(?P<title>\S.+)$")
_NUMBER_RE = re.compile(r"^[+-]?(?:\d[\d,]*)(?:\.\d+)?%?$")
_CJK_RE = re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def _is_cjk(character: str) -> bool:
    return bool(character and _CJK_RE.match(character))


def _escape_table_cell(value: str) -> str:
    return value.replace("\r", "").replace("\n", "<br>").replace("|", "\\|").strip()


def _is_numeric(value: str) -> bool:
    normalized = value.strip().replace(",", "")
    return bool(normalized and _NUMBER_RE.match(normalized))


@dataclass(slots=True)
class PDFToMarkdownConverter:
    """A conservative converter that avoids inventing missing structure."""

    asset_directory_name: str = "assets"

    def convert(self, document: RawDocument) -> str:
        text_blocks = [
            element
            for page in document.pages
            for element in page.elements
            if isinstance(element, RawTextBlock) and element.text.strip()
        ]
        has_table_text = any(
            isinstance(element, RawTable) and any(any(cell for cell in row) for row in element.rows)
            for page in document.pages
            for element in page.elements
        )
        if not text_blocks and not has_table_text:
            raise NoExtractableTextError(document.source_path)

        sizes = [
            span.size
            for block in text_blocks
            for line in block.lines
            for span in line.spans
            if span.text.strip() and span.size > 0
        ]
        body_size = statistics.median(sizes) if sizes else 12.0

        rendered_pages: list[str] = []
        figure_number = 0
        for page in document.pages:
            rendered_elements = [f"<!-- page: {page.page_number} -->"]
            for element in page.elements:
                if isinstance(element, RawTextBlock):
                    rendered = self._render_text_block(element, body_size)
                elif isinstance(element, RawTable):
                    rendered = self._render_table(element)
                elif isinstance(element, RawImage):
                    figure_number += 1
                    rendered = self._render_image(document, element, figure_number)
                else:
                    continue
                if rendered:
                    rendered_elements.append(rendered)
            rendered_pages.append("\n\n".join(rendered_elements))
        return "\n\n".join(rendered_pages).rstrip() + "\n"

    def _render_text_block(self, block: RawTextBlock, body_size: float) -> str:
        lines = [line.text.strip() for line in block.lines if line.text.strip()]
        if not lines:
            return ""
        heading_level = self._heading_level(lines, block, body_size)
        if heading_level is not None:
            return f"{'#' * heading_level} {lines[0]}"
        return self._join_paragraph_lines(lines)

    @staticmethod
    def _heading_level(lines: list[str], block: RawTextBlock, body_size: float) -> int | None:
        if len(lines) != 1:
            return None
        text = lines[0].strip()
        if not text:
            return None
        numbered = _NUMBERED_HEADING_RE.match(text)
        if numbered:
            return min(6, numbered.group("number").count(".") + 1)
        if (
            len(text) <= 120
            and block.max_font_size >= body_size * 1.3
            and text[-1] not in "。！？；：,，;:"
        ):
            return 1
        return None

    @staticmethod
    def _join_paragraph_lines(lines: list[str]) -> str:
        text = lines[0]
        for next_line in lines[1:]:
            if not next_line:
                continue
            if text.endswith("-") and next_line[0].isascii() and next_line[0].isalpha():
                text = text[:-1] + next_line
            elif text and _is_cjk(text[-1]) and _is_cjk(next_line[0]):
                text += next_line
            else:
                text += " " + next_line
        return text.strip()

    def _render_table(self, table: RawTable) -> str:
        rows = table.rows
        if not rows:
            return "[Table with no extractable cells]"
        width = max(len(row) for row in rows)
        normalized = [tuple(list(row) + [""] * (width - len(row))) for row in rows]
        header = normalized[0]
        body = normalized[1:]
        alignments: list[str] = []
        for column_index in range(width):
            values = [row[column_index] for row in body if row[column_index].strip()]
            alignments.append("---:" if values and all(_is_numeric(value) for value in values) else "---")

        lines = [self._table_row(header), "| " + " | ".join(alignments) + " |"]
        lines.extend(self._table_row(row) for row in body)
        return "\n".join(lines)

    @staticmethod
    def _table_row(row: tuple[str, ...]) -> str:
        return "| " + " | ".join(_escape_table_cell(cell) for cell in row) + " |"

    def _render_image(self, document: RawDocument, image: RawImage, figure_number: int) -> str:
        if image.data is not None and image.extension:
            asset_path = f"{self.asset_directory_name}/{document.document_id}/{image.figure_filename}"
            image_markdown = f"![Figure {figure_number}]({asset_path})"
        else:
            image_markdown = f"[Figure on page {image.page_number}]"
        if image.data is not None and image.extension:
            note = f"Figure {figure_number}: image extracted from PDF page {image.page_number}"
        else:
            note = f"Figure {figure_number}: image bytes were not extracted from PDF page {image.page_number}"
        return f"{image_markdown}\n\n> {note}"