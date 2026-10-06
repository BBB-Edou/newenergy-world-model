"""L1: PDF parsing to Markdown and legacy skeleton input contracts."""

from __future__ import annotations

from typing import Any

from .converters import PDFToMarkdownConverter
from .errors import (
    EmptyPDFError,
    InvalidPDFError,
    L1DataError,
    MarkdownReadError,
    NoExtractableTextError,
    OutputPathError,
    PDFBackendUnavailableError,
    PDFError,
    PDFNotFoundError,
    PDFReadError,
)
from .loaders import FileMarkdownLoader, MarkdownLoader, PDFLoader, load_demo_scenario
from .models import (
    BBox,
    Configuration,
    Dataset,
    Document,
    MarkdownDocument,
    NaturalLanguage,
    RawArtifact,
    RawArtifactKind,
    RawDataBundle,
    RawDocument,
    RawImage,
    RawPage,
    RawTable,
    RawTextBlock,
    Table,
    TextLine,
    TextSpan,
)


def __getattr__(name: str) -> Any:
    if name == "L1DataService":
        from .service import L1DataService

        return L1DataService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BBox",
    "Configuration",
    "Dataset",
    "Document",
    "EmptyPDFError",
    "FileMarkdownLoader",
    "InvalidPDFError",
    "L1DataError",
    "L1DataService",
    "MarkdownDocument",
    "MarkdownLoader",
    "MarkdownReadError",
    "NaturalLanguage",
    "NoExtractableTextError",
    "OutputPathError",
    "PDFBackendUnavailableError",
    "PDFError",
    "PDFLoader",
    "PDFNotFoundError",
    "PDFReadError",
    "PDFToMarkdownConverter",
    "RawArtifact",
    "RawArtifactKind",
    "RawDataBundle",
    "RawDocument",
    "RawImage",
    "RawPage",
    "RawTable",
    "RawTextBlock",
    "Table",
    "TextLine",
    "TextSpan",
    "load_demo_scenario",
]