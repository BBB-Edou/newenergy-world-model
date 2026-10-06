"""Standard L1 -> L2 interface for reading generated Markdown."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from l1_data.errors import MarkdownReadError
from l1_data.models import MarkdownDocument


class MarkdownLoader(Protocol):
    """Load a Markdown artifact without invoking an LLM."""

    def load(self, markdown_path: str | Path) -> MarkdownDocument:
        ...


class FileMarkdownLoader:
    """Read UTF-8 Markdown from disk."""

    def load(self, markdown_path: str | Path) -> MarkdownDocument:
        path = Path(markdown_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise MarkdownReadError(path, "file not found")
        if path.suffix.lower() not in {".md", ".markdown"}:
            raise MarkdownReadError(path, "file extension must be .md or .markdown")
        try:
            markdown = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise MarkdownReadError(path, str(exc)) from exc
        return MarkdownDocument(
            document_id=path.stem,
            source_path=str(path),
            markdown_path=str(path),
            markdown=markdown,
            page_count=markdown.count("<!-- page: "),
            metadata={"loader": self.__class__.__name__},
        )