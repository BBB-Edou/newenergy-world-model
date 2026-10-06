"""VerificationAgent wrapper around the deterministic rule engine."""

from __future__ import annotations

from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.verification import VerificationResult
from l2_modeling.verification.rules import verify_knowledge_state


class VerificationAgent:
    def verify(self, state: KnowledgeState) -> VerificationResult:
        return verify_knowledge_state(state)