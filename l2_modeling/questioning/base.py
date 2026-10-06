"""Backward-compatible user-interaction question generation."""

from __future__ import annotations

from typing import Protocol

from l2_modeling.interaction import Question, QuestionSet, generate_questions
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.verification import VerificationResult


class QuestioningService(Protocol):
    def generate_questions(self, knowledge_state: KnowledgeState, verification: VerificationResult) -> QuestionSet:
        ...


PlaceholderQuestioningService = generate_questions

__all__ = ["PlaceholderQuestioningService", "Question", "QuestioningService", "QuestionSet", "generate_questions"]