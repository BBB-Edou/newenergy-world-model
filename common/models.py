"""Layer-neutral value objects shared by the L1-L6 packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import uuid4

Metadata = Mapping[str, Any]


def new_id(prefix: str) -> str:
    """Return a stable-prefix unique identifier for skeleton objects."""

    return f"{prefix}-{uuid4().hex}"


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRef:
    """Traceability record for a fact or model element."""

    source_id: str
    kind: str
    uri: str | None = None
    location: str | None = None
    excerpt: str | None = None
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Confidence:
    """Normalized confidence with an optional explanation."""

    score: float
    rationale: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("confidence score must be between 0.0 and 1.0")