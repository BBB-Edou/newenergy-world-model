"""Clear, layer-specific exceptions for L1 PDF processing."""

from __future__ import annotations

from pathlib import Path


class L1DataError(Exception):
    """Base error for L1 processing."""


class PDFError(L1DataError):
    """Base error for PDF loading or conversion."""


class PDFNotFoundError(PDFError):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        super().__init__(f"PDF file not found: {self.path}")


class InvalidPDFError(PDFError):
    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = Path(path)
        super().__init__(f"Not a readable PDF file: {self.path} ({reason})")


class PDFReadError(PDFError):
    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = Path(path)
        super().__init__(f"Unable to read PDF: {self.path} ({reason})")


class PDFBackendUnavailableError(PDFError):
    def __init__(self) -> None:
        super().__init__("PyMuPDF is required for PDF loading. Install the 'pymupdf' package.")


class EmptyPDFError(PDFError):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        super().__init__(f"PDF contains no pages: {self.path}")


class NoExtractableTextError(PDFError):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        super().__init__(f"PDF has no extractable text: {self.path}")


class OutputPathError(L1DataError):
    pass
class MarkdownReadError(L1DataError):
    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = Path(path)
        super().__init__(f"Unable to read Markdown: {self.path} ({reason})")