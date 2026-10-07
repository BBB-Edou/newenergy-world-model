"""UserInteractionAgent with deterministic question generation and updates."""

from __future__ import annotations

from l2_modeling.interaction import QuestionSet, StateUpdateResult, UserAnswer, apply_answers, generate_questions
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.llm import LLMClient
from l2_modeling.scenario.interaction import apply_scenario_answers, generate_scenario_questions
from l2_modeling.scenario.schema import DataManifest, ScenarioData, ScenarioUpdateResult
from l2_modeling.verification import VerificationResult


class UserInteractionAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self._last_questions = QuestionSet()
        self._last_scenario_questions = QuestionSet()

    def generate_questions(self, state: KnowledgeState, verification: VerificationResult) -> QuestionSet:
        self._last_questions = generate_questions(state, verification)
        return self._last_questions

    def apply_answers(self, state: KnowledgeState, answers: list[UserAnswer]) -> StateUpdateResult:
        return apply_answers(state, answers, self._last_questions)

    def generate_scenario_questions(self, scenario: ScenarioData, verification: VerificationResult) -> QuestionSet:
        self._last_scenario_questions = generate_scenario_questions(verification)
        return self._last_scenario_questions

    def apply_scenario_answers(
        self,
        scenario: ScenarioData,
        manifest: DataManifest,
        answers: list[UserAnswer],
    ) -> ScenarioUpdateResult:
        return apply_scenario_answers(scenario, manifest, answers, self._last_scenario_questions)