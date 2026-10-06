"""Compatibility generator that calls the deterministic KState -> SysML mapper."""

from __future__ import annotations

from typing import Protocol

from l2_modeling.knowledge_state import KnowledgeState
from l3_sysml.mapper import KnowledgeStateToSysMLMapper
from l3_sysml.schema import SysMLModel


class SysMLGenerator(Protocol):
    def generate(self, knowledge_state: KnowledgeState) -> SysMLModel:
        ...


class KnowledgeStateToSysMLGenerator:
    def generate(self, knowledge_state: KnowledgeState) -> SysMLModel:
        return KnowledgeStateToSysMLMapper().map(knowledge_state)