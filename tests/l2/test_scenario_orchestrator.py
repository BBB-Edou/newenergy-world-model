from __future__ import annotations

import json

from l2_modeling import L2Orchestrator, MockLLMClient, RawDocument, UserAnswer
from l2_modeling.demo import _knowledge_state_payload, _requirement_payload, load_demo_document
from l2_modeling.scenario import DataManifest, ScenarioSource


SCENARIO_TABLE = """

| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
| 01:00 | 110 | 0 | 280 | 0.35 |
"""


def _document() -> RawDocument:
    base = load_demo_document()
    return RawDocument(document_id="scenario-doc", filename="scenario.pdf", content=base.content + SCENARIO_TABLE)


def _manifest(units: dict[str, str | None] | None = None) -> dict:
    return DataManifest(
        scenario_id="case-1",
        table_id="table_01",
        time_column="时间",
        columns={"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power", "电价": "electricity_price"},
        units=units or {"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
        time_step="1h",
        source=ScenarioSource(document="scenario.pdf", table_id="table_01", page=1),
    ).model_dump()


def _client(manifest: dict) -> MockLLMClient:
    return MockLLMClient(responses=[json.dumps(_requirement_payload()), json.dumps(_knowledge_state_payload()), json.dumps({"document_id": "scenario-doc", "manifests": [manifest]})])


def test_orchestrator_returns_knowledge_state_and_valid_scenario_data() -> None:
    result = L2Orchestrator(_client(_manifest())).run(_document())

    assert result.status == "VALID"
    assert result.verification_result.status == "VALID"
    assert result.scenario_data is not None
    assert result.scenario_verification is not None
    assert result.scenario_verification.status == "VALID"
    assert result.scenario_data.variables["wind_power"] == [120, 110]


def test_orchestrator_uses_user_answer_for_missing_scenario_unit() -> None:
    missing_unit = _manifest({"wind_power": "kW", "pv_power": "kW", "load_power": "kW"})
    def answer_provider(questions):
        question = next(item for item in questions.questions if item.target_id == "electricity_price")
        return [UserAnswer(question_id=question.question_id, answer="CNY/kWh")]

    result = L2Orchestrator(_client(missing_unit), answer_provider=answer_provider).run(_document())

    assert result.status == "VALID"
    assert result.scenario_data is not None
    assert result.scenario_data.units["electricity_price"] == "CNY/kWh"