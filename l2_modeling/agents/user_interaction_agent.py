"""UserInteractionAgent with deterministic question generation and updates."""

from __future__ import annotations

from l2_modeling.interaction import QuestionSet, StateUpdateResult, UserAnswer, apply_answers, generate_questions
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.llm import LLMClient
from l2_modeling.verification import VerificationResult


class UserInteractionAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self._last_questions = QuestionSet()

    def generate_questions(self, state: KnowledgeState, verification: VerificationResult) -> QuestionSet:
        self._last_questions = generate_questions(state, verification)
        return self._last_questions

    def apply_answers(self, state: KnowledgeState, answers: list[UserAnswer]) -> StateUpdateResult:
        return apply_answers(state, answers, self._last_questions)