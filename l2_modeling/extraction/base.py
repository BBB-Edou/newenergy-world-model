"""Compatibility extraction protocol for deterministic adapters."""

from __future__ import annotations

from typing import Protocol

from l1_data import RawDataBundle
from l2_modeling.knowledge_state import KnowledgeState


class KnowledgeExtractor(Protocol):
    def extract(self, raw_data: RawDataBundle) -> KnowledgeState:
        ...