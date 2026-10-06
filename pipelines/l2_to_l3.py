"""L2 -> L3 pipeline stage."""

from __future__ import annotations

from l2_modeling import KnowledgeState
from l3_sysml import KnowledgeStateToSysMLGenerator, SysMLGenerator, SysMLModel


def run_l2_to_l3(knowledge_state: KnowledgeState, *, generator: SysMLGenerator | None = None) -> SysMLModel:
    return (generator or KnowledgeStateToSysMLGenerator()).generate(knowledge_state)