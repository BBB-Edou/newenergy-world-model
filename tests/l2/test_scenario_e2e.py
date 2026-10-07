from __future__ import annotations

import json
from pathlib import Path

from l2_modeling import L2Orchestrator, MockLLMClient, RawDocument
from l2_modeling.demo import _knowledge_state_payload, _requirement_payload, load_demo_document
from l2_modeling.scenario import ScenarioInputBinding, export_scenario_csv
from l3_sysml import KnowledgeStateToSysMLGenerator
from l4_compiler import ModelCompiler, validate_world_model


SCENARIO_TABLE = """

| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
| 01:00 | 110 | 0 | 280 | 0.35 |
"""
MANIFEST = {
    "scenario_id": "case-1",
    "table_id": "table_01",
    "time_column": "时间",
    "columns": {"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power", "电价": "electricity_price"},
    "units": {"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
    "time_step": "1h",
    "source": {"document": "scenario.pdf", "table_id": "table_01", "page": 1},
}


def _document() -> RawDocument:
    base = load_demo_document()
    return RawDocument(document_id="scenario-doc", filename="scenario.pdf", content=base.content + SCENARIO_TABLE)


def _client() -> MockLLMClient:
    return MockLLMClient(responses=[json.dumps(_requirement_payload()), json.dumps(_knowledge_state_payload()), json.dumps({"document_id": "scenario-doc", "manifests": [MANIFEST]})])


def test_l2_scenario_to_l4_and_l5_input_binding(tmp_path: Path) -> None:
    l2_result = L2Orchestrator(_client()).run(_document())
    assert l2_result.status == "VALID"
    assert l2_result.scenario_data is not None

    sysml_model = KnowledgeStateToSysMLGenerator().generate(l2_result.knowledge_state)
    world_model = ModelCompiler().compile(sysml_model)
    binding = ScenarioInputBinding(world_model_ir_id=world_model.metadata.ir_id, scenario_id=l2_result.scenario_data.scenario_id)
    csv_path = tmp_path / "scenario.csv"
    csv_content = export_scenario_csv(l2_result.scenario_data, csv_path)

    assert validate_world_model(world_model).valid
    assert binding.status == "READY"
    assert csv_path.read_text(encoding="utf-8") == csv_content
    assert "timestamp,wind_power,pv_power,load_power,electricity_price" in csv_content


def test_scenario_pipeline_is_deterministic() -> None:
    first = L2Orchestrator(_client()).run(_document())
    second = L2Orchestrator(_client()).run(_document())

    assert first.scenario_data == second.scenario_data
    assert export_scenario_csv(first.scenario_data) == export_scenario_csv(second.scenario_data)