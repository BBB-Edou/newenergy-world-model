"""Synchronous L2 orchestration for KnowledgeState and ScenarioData."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from l2_modeling.agents.modeling_agent import ModelingAgent
from l2_modeling.agents.requirement_agent import RequirementAgent
from l2_modeling.agents.user_interaction_agent import UserInteractionAgent
from l2_modeling.agents.verification_agent import VerificationAgent
from l2_modeling.extraction.schema import RawDocument, RequirementExtraction
from l2_modeling.interaction import Question, QuestionSet, UserAnswer
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.llm import LLMClient
from l2_modeling.scenario import DataManifest, ScenarioBuildError, ScenarioData, ScenarioDataExtractor, build_scenario_data
from l2_modeling.verification import VerificationResult

AnswerProvider = Callable[[QuestionSet], list[UserAnswer]]


class L2PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["VALID", "NEED_USER_INPUT", "FAILED"]
    requirement_extraction: RequirementExtraction
    knowledge_state: KnowledgeState
    verification_result: VerificationResult
    questions: QuestionSet | None = None
    data_manifest: DataManifest | None = None
    scenario_data: ScenarioData | None = None
    scenario_verification: VerificationResult | None = None
    scenario_questions: QuestionSet | None = None


class L2Orchestrator:
    def __init__(self, llm_client: LLMClient, answer_provider: AnswerProvider | None = None) -> None:
        self.requirement_agent = RequirementAgent(llm_client)
        self.modeling_agent = ModelingAgent(llm_client)
        self.verification_agent = VerificationAgent()
        self.user_interaction_agent = UserInteractionAgent(llm_client)
        self.scenario_extractor = ScenarioDataExtractor(llm_client)
        self.answer_provider = answer_provider

    def run(self, document: RawDocument, max_interaction_rounds: int = 5) -> L2PipelineResult:
        if max_interaction_rounds < 0:
            raise ValueError("max_interaction_rounds must be non-negative")

        extraction = self.requirement_agent.run(document)
        state = self.modeling_agent.run(extraction)
        verification = self.verification_agent.verify(state)

        if verification.status == "VALID":
            return self._with_scenario_result(document, extraction, state, verification, max_interaction_rounds)
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
                return self._with_scenario_result(document, extraction, state, verification, max_interaction_rounds)
            if verification.status == "INVALID":
                return self._result("FAILED", extraction, state, verification)
            questions = self.user_interaction_agent.generate_questions(state, verification)

        return self._result("NEED_USER_INPUT", extraction, state, verification, questions)
    def _with_scenario_result(
        self,
        document: RawDocument,
        extraction: RequirementExtraction,
        state: KnowledgeState,
        verification: VerificationResult,
        max_interaction_rounds: int,
    ) -> L2PipelineResult:
        scenario_extraction = self.scenario_extractor.extract(document)
        if not scenario_extraction.manifests:
            if self.scenario_extractor.last_candidates:
                question = Question(
                    question_id="scenario-q-manifest",
                    question_type="clarification",
                    target_type="scenario_manifest",
                    target_field="manifest",
                    question="请确认候选表格是否属于运行场景数据。",
                    reason="candidate scenario tables were detected but no manifest was produced",
                )
                return self._result("NEED_USER_INPUT", extraction, state, verification, scenario_questions=QuestionSet(questions=[question]))
            return self._result("VALID", extraction, state, verification)

        manifest = scenario_extraction.manifests[0]
        candidate = next((item for item in self.scenario_extractor.last_candidates if item.table_id == manifest.table_id), None)
        if candidate is None:
            return self._result("FAILED", extraction, state, verification, scenario_verification=VerificationResult(status="INVALID"))
        try:
            scenario = build_scenario_data(manifest, candidate)
        except ScenarioBuildError as exc:
            question = Question(
                question_id="scenario-q-build",
                question_type="clarification",
                target_type="scenario_manifest",
                target_id=manifest.scenario_id,
                target_field="columns",
                question="请确认识别出的场景列是否存在于原始表格。",
                reason=str(exc),
            )
            return self._result("NEED_USER_INPUT", extraction, state, verification, data_manifest=manifest, scenario_questions=QuestionSet(questions=[question]))
        scenario_verification = self.verification_agent.verify_scenario_data(scenario)
        scenario_questions: QuestionSet | None = None

        for _ in range(max_interaction_rounds):
            if scenario_verification.status == "VALID":
                return self._result("VALID", extraction, state, verification, data_manifest=manifest, scenario_data=scenario, scenario_verification=scenario_verification)
            if scenario_verification.status == "INVALID":
                return self._result("FAILED", extraction, state, verification, data_manifest=manifest, scenario_data=scenario, scenario_verification=scenario_verification)
            scenario_questions = self.user_interaction_agent.generate_scenario_questions(scenario, scenario_verification)
            if self.answer_provider is None:
                return self._result("NEED_USER_INPUT", extraction, state, verification, scenario_questions=scenario_questions, data_manifest=manifest, scenario_data=scenario, scenario_verification=scenario_verification)
            answers = self.answer_provider(scenario_questions)
            if not answers:
                return self._result("NEED_USER_INPUT", extraction, state, verification, scenario_questions=scenario_questions, data_manifest=manifest, scenario_data=scenario, scenario_verification=scenario_verification)
            update = self.user_interaction_agent.apply_scenario_answers(scenario, manifest, answers)
            if not update.updated:
                return self._result("NEED_USER_INPUT", extraction, state, verification, scenario_questions=scenario_questions, data_manifest=manifest, scenario_data=scenario, scenario_verification=scenario_verification)
            scenario = update.scenario_data
            manifest = update.data_manifest
            scenario_verification = self.verification_agent.verify_scenario_data(scenario)

        return self._result("NEED_USER_INPUT", extraction, state, verification, scenario_questions=scenario_questions, data_manifest=manifest, scenario_data=scenario, scenario_verification=scenario_verification)
    @staticmethod
    def _result(
        status: Literal["VALID", "NEED_USER_INPUT", "FAILED"],
        extraction: RequirementExtraction,
        state: KnowledgeState,
        verification: VerificationResult,
        questions: QuestionSet | None = None,
        data_manifest: DataManifest | None = None,
        scenario_data: ScenarioData | None = None,
        scenario_verification: VerificationResult | None = None,
        scenario_questions: QuestionSet | None = None,
    ) -> L2PipelineResult:
        return L2PipelineResult(
            status=status,
            requirement_extraction=extraction,
            knowledge_state=state,
            verification_result=verification,
            questions=questions,
            data_manifest=data_manifest,
            scenario_data=scenario_data,
            scenario_verification=scenario_verification,
            scenario_questions=scenario_questions,
        )