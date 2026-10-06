"""Pydantic schemas exchanged by the L2 extraction agents."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractionSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RawDocument(ExtractionSchemaModel):
    document_id: str
    content: str
    content_type: str = "markdown"
    filename: str | None = None

    @classmethod
    def from_markdown_document(cls, document: object) -> "RawDocument":
        path_text = str(getattr(document, "markdown_path"))
        return cls(
            document_id=str(getattr(document, "document_id")),
            content=str(getattr(document, "markdown")),
            content_type="markdown",
            filename=path_text.replace("\\", "/").rsplit("/", maxsplit=1)[-1],
        )


class ExtractionItem(ExtractionSchemaModel):
    id: str
    category: Literal["entity", "attribute", "state", "relation", "process", "constraint", "objective", "unknown"]
    name: str
    description: str | None = None
    value: Any | None = None
    unit: str | None = None


class RequirementExtraction(ExtractionSchemaModel):
    document_id: str
    items: list[ExtractionItem] = Field(default_factory=list)