"""VerificationAgent wrapper around the deterministic rule engine."""

from __future__ import annotations

from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.scenario.schema import ScenarioData
from l2_modeling.scenario.validator import validate_scenario_data
from l2_modeling.verification import VerificationResult
from l2_modeling.verification.rules import verify_knowledge_state


class VerificationAgent:
    def verify(self, state: KnowledgeState) -> VerificationResult:
        return verify_knowledge_state(state)

    def verify_scenario_data(self, scenario: ScenarioData) -> VerificationResult:
        return validate_scenario_data(scenario)