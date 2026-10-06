"""L1 input and intermediate contracts.

These objects describe source material only. They do not contain interpreted
energy-domain facts; interpretation belongs to L2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator, Mapping, TypeAlias

from common import Metadata, SourceRef


class RawArtifactKind(str, Enum):
    DOCUMENT = "document"
    TABLE = "table"
    DATASET = "dataset"
    NATURAL_LANGUAGE = "natural_language"
    CONFIGURATION = "configuration"


@dataclass(frozen=True, slots=True, kw_only=True)
class RawArtifact:
    artifact_id: str
    name: str
    kind: RawArtifactKind
    source: SourceRef
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Document(RawArtifact):
    text: str
    mime_type: str = "text/plain"
    kind: RawArtifactKind = field(default=RawArtifactKind.DOCUMENT, init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class Table(RawArtifact):
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...] = ()
    kind: RawArtifactKind = field(default=RawArtifactKind.TABLE, init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class Dataset(RawArtifact):
    format: str
    records: tuple[Mapping[str, Any], ...] = ()
    kind: RawArtifactKind = field(default=RawArtifactKind.DATASET, init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class NaturalLanguage(RawArtifact):
    text: str
    language: str | None = None
    kind: RawArtifactKind = field(default=RawArtifactKind.NATURAL_LANGUAGE, init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration(RawArtifact):
    values: Mapping[str, Any]
    kind: RawArtifactKind = field(default=RawArtifactKind.CONFIGURATION, init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class RawDataBundle:
    """Single L1 -> L2 transport object for non-PDF skeleton inputs."""

    bundle_id: str
    artifacts: tuple[RawArtifact, ...] = ()
    source_directory: str | None = None
    metadata: Metadata = field(default_factory=dict)

    def by_kind(self, kind: RawArtifactKind) -> Iterator[RawArtifact]:
        return (artifact for artifact in self.artifacts if artifact.kind is kind)


@dataclass(frozen=True, slots=True, kw_only=True)
class BBox:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def area(self) -> float:
        return self.width * self.height

    def overlap_ratio(self, other: "BBox") -> float:
        width = max(0.0, min(self.x1, other.x1) - max(self.x0, other.x0))
        height = max(0.0, min(self.y1, other.y1) - max(self.y0, other.y0))
        intersection = width * height
        if intersection <= 0 or self.area <= 0:
            return 0.0
        return intersection / self.area


@dataclass(frozen=True, slots=True, kw_only=True)
class TextSpan:
    text: str
    size: float
    font: str | None = None
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class TextLine:
    text: str
    bbox: BBox
    spans: tuple[TextSpan, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class RawTextBlock:
    block_id: str
    bbox: BBox
    lines: tuple[TextLine, ...] = ()

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines).strip()

    @property
    def max_font_size(self) -> float:
        return max((span.size for line in self.lines for span in line.spans), default=0.0)


@dataclass(frozen=True, slots=True, kw_only=True)
class RawTable:
    table_id: str
    bbox: BBox
    rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class RawImage:
    figure_id: str
    page_number: int
    bbox: BBox
    extension: str | None = None
    data: bytes | None = None
    width: int | None = None
    height: int | None = None

    @property
    def figure_filename(self) -> str:
        extension = (self.extension or "png").lower().lstrip(".")
        return f"page_{self.page_number:04d}_figure_{self.figure_id.rsplit('-', 1)[-1]}.{extension}"


RawPageElement: TypeAlias = RawTextBlock | RawTable | RawImage


@dataclass(frozen=True, slots=True, kw_only=True)
class RawPage:
    page_number: int
    width: float
    height: float
    elements: tuple[RawPageElement, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class RawDocument:
    document_id: str
    source_path: str
    page_count: int
    pages: tuple[RawPage, ...] = ()
    title: str | None = None
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class MarkdownDocument:
    document_id: str
    source_path: str
    markdown_path: str
    markdown: str
    page_count: int
    title: str | None = None
    metadata: Metadata = field(default_factory=dict)