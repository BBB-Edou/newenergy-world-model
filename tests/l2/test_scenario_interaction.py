from __future__ import annotations

from l2_modeling import MockLLMClient, UserAnswer, UserInteractionAgent, VerificationAgent
from l2_modeling.scenario import DataManifest, ScenarioSource, build_scenario_data, detect_markdown_tables


MARKDOWN = """| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
| 01:00 | 110 | 0 | 280 | 0.35 |
"""


def _manifest(units=None) -> DataManifest:
    return DataManifest(
        scenario_id="case-1",
        table_id="table_01",
        time_column="时间",
        columns={"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power", "电价": "electricity_price"},
        units=units or {"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
        time_step="1h",
        source=ScenarioSource(document="case.pdf", table_id="table_01", page=1),
    )


def test_scenario_unit_answer_updates_manifest_and_can_validate() -> None:
    manifest = _manifest({"wind_power": "kW", "pv_power": "kW", "load_power": "kW"})
    scenario = build_scenario_data(manifest, detect_markdown_tables(MARKDOWN)[0])
    verification = VerificationAgent().verify_scenario_data(scenario)
    agent = UserInteractionAgent(MockLLMClient([]))
    questions = agent.generate_scenario_questions(scenario, verification)
    question = next(item for item in questions.questions if item.target_id == "electricity_price")

    update = agent.apply_scenario_answers(scenario, manifest, [UserAnswer(question_id=question.question_id, answer="CNY/kWh")])

    assert update.updated
    assert update.data_manifest.units["electricity_price"] == "CNY/kWh"
    assert update.scenario_data.units["electricity_price"] == "CNY/kWh"
    assert VerificationAgent().verify_scenario_data(update.scenario_data).status == "VALID"


def test_scenario_missing_value_answer_updates_only_target_cell() -> None:
    markdown = MARKDOWN.replace("| 01:00 | 110 |", "| 01:00 | - |")
    manifest = _manifest()
    scenario = build_scenario_data(manifest, detect_markdown_tables(markdown)[0])
    verification = VerificationAgent().verify_scenario_data(scenario)
    agent = UserInteractionAgent(MockLLMClient([]))
    questions = agent.generate_scenario_questions(scenario, verification)
    question = next(item for item in questions.questions if item.target_id == "wind_power:1")

    update = agent.apply_scenario_answers(scenario, manifest, [UserAnswer(question_id=question.question_id, answer="110")])

    assert update.updated
    assert update.scenario_data.variables["wind_power"] == [120, 110]
    assert VerificationAgent().verify_scenario_data(update.scenario_data).status == "VALID"