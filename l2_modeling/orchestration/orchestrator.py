"""Synchronous L2 orchestration with a finite interaction loop."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from l2_modeling.agents.modeling_agent import ModelingAgent
from l2_modeling.agents.requirement_agent import RequirementAgent
from l2_modeling.agents.user_interaction_agent import UserInteractionAgent
from l2_modeling.agents.verification_agent import VerificationAgent
from l2_modeling.extraction.schema import RawDocument, RequirementExtraction
from l2_modeling.interaction import QuestionSet, UserAnswer
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.llm import LLMClient
from l2_modeling.verification import VerificationResult

AnswerProvider = Callable[[QuestionSet], list[UserAnswer]]


class L2PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["VALID", "NEED_USER_INPUT", "FAILED"]
    requirement_extraction: RequirementExtraction
    knowledge_state: KnowledgeState
    verification_result: VerificationResult
    questions: QuestionSet | None = None


class L2Orchestrator:
    def __init__(self, llm_client: LLMClient, answer_provider: AnswerProvider | None = None) -> None:
        self.requirement_agent = RequirementAgent(llm_client)
        self.modeling_agent = ModelingAgent(llm_client)
        self.verification_agent = VerificationAgent()
        self.user_interaction_agent = UserInteractionAgent(llm_client)
        self.answer_provider = answer_provider

    def run(self, document: RawDocument, max_interaction_rounds: int = 5) -> L2PipelineResult:
        if max_interaction_rounds < 0:
            raise ValueError("max_interaction_rounds must be non-negative")

        extraction = self.requirement_agent.run(document)
        state = self.modeling_agent.run(extraction)
        verification = self.verification_agent.verify(state)

        if verification.status == "VALID":
            return self._result("VALID", extraction, state, verification)
        if verification.status == "INVALID":
            return self._result("FAILED", extraction, state, verification)

        questions = self.user_interaction_agent.generate_questions(state, verification)
        for _ in range(max_interaction_rounds):
            if self.answer_provider is None:
                return self._result("NEED_USER_INPUT", extraction, state, verification, questions)
            answers = self.answer_provider(questions)
            if not answers:
                return self._result("NEED_USER_INPUT", extraction, state, verification, questions)

            update = self.user_interaction_agent.apply_answers(state, answers)
            if not update.updated:
                return self._result("NEED_USER_INPUT", extraction, state, verification, questions)
            state = update.knowledge_state
            verification = self.verification_agent.verify(state)
            if verification.status == "VALID":
                return self._result("VALID", extraction, state, verification)
            if verification.status == "INVALID":
                return self._result("FAILED", extraction, state, verification)
            questions = self.user_interaction_agent.generate_questions(state, verification)

        return self._result("NEED_USER_INPUT", extraction, state, verification, questions)

    @staticmethod
    def _result(
        status: Literal["VALID", "NEED_USER_INPUT", "FAILED"],
        extraction: RequirementExtraction,
        state: KnowledgeState,
        verification: VerificationResult,
        questions: QuestionSet | None = None,
    ) -> L2PipelineResult:
        return L2PipelineResult(
            status=status,
            requirement_extraction=extraction,
            knowledge_state=state,
            verification_result=verification,
            questions=questions,
        )