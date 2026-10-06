"""L1 service and CLI: PDF -> Markdown only."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from l1_data.converters import PDFToMarkdownConverter
from l1_data.errors import OutputPathError
from l1_data.loaders import PDFLoader
from l1_data.loaders.markdown_loader import FileMarkdownLoader, MarkdownLoader
from l1_data.models import MarkdownDocument, RawDocument, RawImage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "markdown"


class L1DataService:
    """Orchestrate PDF loading, Markdown conversion and file persistence."""

    def __init__(
        self,
        *,
        loader: PDFLoader | None = None,
        converter: PDFToMarkdownConverter | None = None,
        markdown_loader: MarkdownLoader | None = None,
    ) -> None:
        self.loader = loader or PDFLoader()
        self.converter = converter or PDFToMarkdownConverter()
        self.markdown_loader = markdown_loader or FileMarkdownLoader()

    def process_pdf(
        self,
        pdf_path: str | Path,
        *,
        output_dir: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        document = self.loader.load(pdf_path)
        markdown = self.converter.convert(document)
        target = self._resolve_output_path(document.document_id, output_dir, output_path)

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputPathError(f"Unable to create output directory: {target.parent} ({exc})") from exc
        if target.exists() and target.is_dir():
            raise OutputPathError(f"Output path points to a directory: {target}")

        try:
            target.write_text(markdown, encoding="utf-8", newline="\n")
        except OSError as exc:
            raise OutputPathError(f"Unable to write Markdown: {target} ({exc})") from exc

        self._write_images(document, target.parent)
        return target

    def read_markdown(self, markdown_path: str | Path) -> MarkdownDocument:
        """Standard L1 -> L2 read interface."""

        return self.markdown_loader.load(markdown_path)

    @staticmethod
    def _resolve_output_path(
        document_id: str,
        output_dir: str | Path | None,
        output_path: str | Path | None,
    ) -> Path:
        if output_path is not None:
            return Path(output_path).expanduser().resolve()
        return (Path(output_dir).expanduser().resolve() if output_dir else DEFAULT_OUTPUT_DIR) / f"{document_id}.md"

    @staticmethod
    def _write_images(document: RawDocument, markdown_directory: Path) -> None:
        image_elements = [
            element
            for page in document.pages
            for element in page.elements
            if isinstance(element, RawImage)
        ]
        if not image_elements:
            return
        asset_directory = markdown_directory / "assets" / document.document_id
        for image in image_elements:
            if image.data is None or not image.extension:
                continue
            asset_directory.mkdir(parents=True, exist_ok=True)
            (asset_directory / image.figure_filename).write_bytes(image.data)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert one PDF into structured Markdown (L1 only).")
    parser.add_argument("pdf", type=Path, help="Input PDF file")
    parser.add_argument("-o", "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output", type=Path, default=None, help="Explicit output .md path")
    args = parser.parse_args(argv)

    service = L1DataService()
    input_path = args.pdf.expanduser().resolve()
    output_path = service.process_pdf(input_path, output_dir=args.output_dir, output_path=args.output)

    print("Input:")
    print(input_path)
    print()
    print("Output:")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())