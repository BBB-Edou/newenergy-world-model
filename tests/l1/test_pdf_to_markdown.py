from __future__ import annotations

from pathlib import Path

import pytest

from l1_data import (
    BBox,
    InvalidPDFError,
    L1DataService,
    NoExtractableTextError,
    PDFLoader,
    PDFNotFoundError,
    PDFToMarkdownConverter,
    RawDocument,
    RawImage,
    RawPage,
    RawTextBlock,
    TextLine,
    TextSpan,
)


ROOT = Path(__file__).resolve().parents[2]
DEMO_PDF = ROOT / "examples" / "renewable_energy" / "pdf" / "demo.pdf"


def test_pdf_can_be_converted_to_markdown() -> None:
    document = PDFLoader().load(DEMO_PDF)
    markdown = PDFToMarkdownConverter().convert(document)

    assert "# 1 System Overview" in markdown
    assert "## 1.1 Wind System" in markdown
    assert "<!-- page: 1 -->" in markdown
    assert "<!-- page: 2 -->" in markdown


def test_markdown_file_is_generated(tmp_path: Path) -> None:
    service = L1DataService()

    output_path = service.process_pdf(DEMO_PDF, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.suffix == ".md"
    assert output_path.read_text(encoding="utf-8").startswith("<!-- page: 1 -->")


def test_heading_levels_are_preserved() -> None:
    markdown = PDFToMarkdownConverter().convert(PDFLoader().load(DEMO_PDF))

    assert "# 1 System Overview" in markdown
    assert "## 1.1 Wind System" in markdown
    assert "# 2 Data Table" in markdown


def test_normal_text_is_preserved() -> None:
    markdown = PDFToMarkdownConverter().convert(PDFLoader().load(DEMO_PDF))

    assert "This demo document describes a generic renewable energy system." in markdown
    assert "Wind generation is represented as a placeholder component in this demo." in markdown
    assert "End of L1 demo document." in markdown


def test_simple_table_is_converted_to_markdown_table() -> None:
    markdown = PDFToMarkdownConverter().convert(PDFLoader().load(DEMO_PDF))

    assert "| Entity | Parameter | Value | Unit |" in markdown
    assert "| Battery | Capacity | 200 | kWh |" in markdown
    assert "| Battery | Efficiency | 0.95 | - |" in markdown


def test_page_boundaries_are_preserved() -> None:
    markdown = PDFToMarkdownConverter().convert(PDFLoader().load(DEMO_PDF))

    assert markdown.count("<!-- page: ") == 2
    assert "<!-- page: 1 -->" in markdown
    assert "<!-- page: 2 -->" in markdown


def test_missing_pdf_has_clear_error() -> None:
    missing = DEMO_PDF.parent / "does_not_exist.pdf"

    with pytest.raises(PDFNotFoundError, match="PDF file not found"):
        PDFLoader().load(missing)


def test_blank_pdf_has_clear_no_text_error(tmp_path: Path) -> None:
    import pymupdf

    blank_pdf = tmp_path / "blank.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(blank_pdf)
    document.close()

    with pytest.raises(NoExtractableTextError, match="no extractable text"):
        PDFLoader().load(blank_pdf)


def test_loader_reads_generated_markdown(tmp_path: Path) -> None:
    service = L1DataService()
    output_path = service.process_pdf(DEMO_PDF, output_dir=tmp_path)

    markdown_document = service.read_markdown(output_path)

    assert markdown_document.page_count == 2
    assert "# 1 System Overview" in markdown_document.markdown


def test_image_without_extracted_bytes_uses_placeholder() -> None:
    text_block = RawTextBlock(
        block_id="text-1",
        bbox=BBox(x0=10, y0=10, x1=90, y1=30),
        lines=(
            TextLine(
                text="L1 Image Placeholder",
                bbox=BBox(x0=10, y0=10, x1=90, y1=30),
                spans=(TextSpan(text="L1 Image Placeholder", size=16),),
            ),
        ),
    )
    document = RawDocument(
        document_id="image-demo",
        source_path="image-demo.pdf",
        page_count=1,
        pages=(
            RawPage(
                page_number=1,
                width=100,
                height=100,
                elements=(
                    text_block,
                    RawImage(
                        figure_id="image-demo-p0001-f001",
                        page_number=1,
                        bbox=BBox(x0=0, y0=40, x1=20, y1=60),
                    ),
                ),
            ),
        ),
    )

    markdown = PDFToMarkdownConverter().convert(document)

    assert "[Figure on page 1]" in markdown

def test_extracted_image_bytes_are_saved_next_to_markdown(tmp_path: Path) -> None:
    text_block = RawTextBlock(
        block_id="text-1",
        bbox=BBox(x0=10, y0=10, x1=90, y1=30),
        lines=(
            TextLine(
                text="L1 Image Demo",
                bbox=BBox(x0=10, y0=10, x1=90, y1=30),
                spans=(TextSpan(text="L1 Image Demo", size=16),),
            ),
        ),
    )
    image = RawImage(
        figure_id="image-demo-p0001-f001",
        page_number=1,
        bbox=BBox(x0=0, y0=40, x1=20, y1=60),
        extension="png",
        data=b"fake-png-bytes",
    )
    source_document = RawDocument(
        document_id="image-demo",
        source_path="image-demo.pdf",
        page_count=1,
        pages=(RawPage(page_number=1, width=100, height=100, elements=(text_block, image)),),
    )

    class FakeLoader:
        def load(self, _pdf_path: object) -> RawDocument:
            return source_document

    class FakeConverter:
        def convert(self, document: RawDocument) -> str:
            return f"![Figure 1](assets/{document.document_id}/{image.figure_filename})"

    service = L1DataService(loader=FakeLoader(), converter=FakeConverter())  # type: ignore[arg-type]
    output_path = service.process_pdf("image-demo.pdf", output_dir=tmp_path)

    asset_path = tmp_path / "assets" / "image-demo" / image.figure_filename
    assert output_path.exists()
    assert asset_path.read_bytes() == b"fake-png-bytes"

def test_non_pdf_file_has_clear_error(tmp_path: Path) -> None:
    text_file = tmp_path / "not_a_pdf.pdf"
    text_file.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(InvalidPDFError, match="missing %PDF- signature"):
        PDFLoader().load(text_file)


def test_missing_output_directory_is_created(tmp_path: Path) -> None:
    nested_output = tmp_path / "nested" / "markdown"

    output_path = L1DataService().process_pdf(DEMO_PDF, output_dir=nested_output)

    assert output_path.parent == nested_output
    assert nested_output.is_dir()