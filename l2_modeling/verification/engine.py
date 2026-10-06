"""VerificationAgent implementation."""

from __future__ import annotations

from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.verification.rules import verify_knowledge_state
from l2_modeling.verification.schema import VerificationResult


class VerificationAgent:
    def verify(self, state: KnowledgeState) -> VerificationResult:
        return verify_knowledge_state(state)