"""Offline demo for the L2 KnowledgeState + ScenarioData side channel."""

from __future__ import annotations

import json
from pathlib import Path

from l1_data import FileMarkdownLoader
from l2_modeling import L2Orchestrator, MockLLMClient, RawDocument, ScenarioInputBinding
from l2_modeling.demo import _knowledge_state_payload, _requirement_payload
from l2_modeling.scenario import export_scenario_csv
from l3_sysml import KnowledgeStateToSysMLGenerator
from l4_compiler import ModelCompiler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_MARKDOWN = PROJECT_ROOT / "examples" / "renewable_energy" / "scenario_data" / "demo_scenario.md"
CSV_OUTPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "scenario_data" / "scenario_data.csv"
JSON_OUTPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "scenario_data" / "scenario_data.json"
MANIFEST = {
    "scenario_id": "renewable_energy_demo",
    "table_id": "table_01",
    "time_column": "时间",
    "columns": {"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power", "电价": "electricity_price"},
    "units": {"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
    "time_step": "1h",
    "source": {"document": "demo_scenario.md", "table_id": "table_01", "page": None},
}


def run_demo() -> int:
    l1_document = FileMarkdownLoader().load(SCENARIO_MARKDOWN)
    document = RawDocument.from_markdown_document(l1_document)
    client = MockLLMClient(responses=[json.dumps(_requirement_payload()), json.dumps(_knowledge_state_payload()), json.dumps({"document_id": document.document_id, "manifests": [MANIFEST]})])
    result = L2Orchestrator(client).run(document)
    if result.scenario_data is None:
        print("ScenarioData was not produced")
        return 1
    export_scenario_csv(result.scenario_data, CSV_OUTPUT)
    JSON_OUTPUT.write_text(result.scenario_data.model_dump_json(indent=2) + "\n", encoding="utf-8")
    sysml_model = KnowledgeStateToSysMLGenerator().generate(result.knowledge_state)
    world_model = ModelCompiler().compile(sysml_model)
    binding = ScenarioInputBinding(world_model_ir_id=world_model.metadata.ir_id, scenario_id=result.scenario_data.scenario_id)
    print(f"L2 status: {result.status}")
    print(f"Knowledge entities: {len(result.knowledge_state.entities)}")
    print(f"Scenario rows: {len(result.scenario_data.time)}")
    print(f"Scenario variables: {', '.join(sorted(result.scenario_data.variables))}")
    print(f"WorldModelIR entities: {len(world_model.entities)}")
    print(f"L5 binding: {binding.status}")
    print(f"Scenario JSON: {JSON_OUTPUT}")
    print(f"Scenario CSV: {CSV_OUTPUT}")
    return 0 if result.status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(run_demo())