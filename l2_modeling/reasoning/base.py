"""Reasoning can enrich but must not bypass the Knowledge State contract."""

from __future__ import annotations

from typing import Protocol

from l2_modeling.knowledge_state import KnowledgeState


class ReasoningService(Protocol):
    def infer(self, knowledge_state: KnowledgeState) -> KnowledgeState:
        """Return an enriched Knowledge State."""
        ...


class PlaceholderReasoningService:
    """Phase 0 no-op reasoning implementation."""

    def infer(self, knowledge_state: KnowledgeState) -> KnowledgeState:
        return knowledge_state