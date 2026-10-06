"""Offline L2 demo using a scripted client. It never calls the network."""

from __future__ import annotations

import json
from pathlib import Path

from l1_data import FileMarkdownLoader
from l2_modeling import L2Orchestrator, MockLLMClient, RawDocument

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_MARKDOWN = PROJECT_ROOT / "examples" / "renewable_energy" / "l2" / "demo_system.md"


def _requirement_payload() -> dict:
    return {
        "document_id": "renewable_energy_l2_demo",
        "items": [
            {"id": "wind", "category": "entity", "name": "Wind", "description": "renewable generation", "value": None, "unit": None},
            {"id": "pv", "category": "entity", "name": "PV", "description": "renewable generation", "value": None, "unit": None},
            {"id": "battery", "category": "entity", "name": "Battery", "description": "storage", "value": None, "unit": None},
            {"id": "grid", "category": "entity", "name": "Grid", "description": "grid connection", "value": None, "unit": None},
            {"id": "load", "category": "entity", "name": "Load", "description": "demand", "value": None, "unit": None},
        ],
    }


def _knowledge_state_payload() -> dict:
    return {
        "schema_version": "1.0",
        "entities": [
            {"id": "wind", "name": "Wind", "entity_type": "renewable_source", "description": None},
            {"id": "pv", "name": "PV", "entity_type": "renewable_source", "description": None},
            {"id": "battery", "name": "Battery", "entity_type": "storage", "description": None},
            {"id": "grid", "name": "Grid", "entity_type": "grid_connection", "description": None},
            {"id": "load", "name": "Load", "entity_type": "demand", "description": None},
        ],
        "attributes": [
            {"id": "wind_rated_power", "entity_id": "wind", "name": "rated_power", "value": 100, "unit": "kW", "description": None},
            {"id": "pv_rated_power", "entity_id": "pv", "name": "rated_power", "value": 80, "unit": "kW", "description": None},
            {"id": "battery_capacity", "entity_id": "battery", "name": "capacity", "value": 200, "unit": "kWh", "description": None},
            {"id": "battery_max_charge_power", "entity_id": "battery", "name": "max_charge_power", "value": 50, "unit": "kW", "description": None},
            {"id": "battery_max_discharge_power", "entity_id": "battery", "name": "max_discharge_power", "value": 50, "unit": "kW", "description": None},
            {"id": "battery_soc_min", "entity_id": "battery", "name": "SOC_min", "value": 20, "unit": "%", "description": None},
            {"id": "battery_soc_max", "entity_id": "battery", "name": "SOC_max", "value": 90, "unit": "%", "description": None},
            {"id": "grid_max_import_power", "entity_id": "grid", "name": "max_import_power", "value": 150, "unit": "kW", "description": None},
            {"id": "load_demand", "entity_id": "load", "name": "demand", "value": 120, "unit": "kW", "description": None},
        ],
        "states": [
            {"id": "battery_soc", "entity_id": "battery", "name": "SOC", "value": 50, "unit": "%", "description": None}
        ],
        "relations": [
            {"id": "wind_to_load", "relation_type": "supplies", "source_entity_id": "wind", "target_entity_id": "load", "description": None},
            {"id": "pv_to_load", "relation_type": "supplies", "source_entity_id": "pv", "target_entity_id": "load", "description": None},
            {"id": "battery_to_load", "relation_type": "supplies", "source_entity_id": "battery", "target_entity_id": "load", "description": None},
            {"id": "grid_to_load", "relation_type": "supplies", "source_entity_id": "grid", "target_entity_id": "load", "description": None},
        ],
        "processes": [
            {"id": "generation", "name": "generation", "description": None, "inputs": ["wind", "pv"], "outputs": ["load"]},
            {"id": "charging", "name": "charging", "description": None, "inputs": ["grid"], "outputs": ["battery"]},
            {"id": "discharging", "name": "discharging", "description": None, "inputs": ["battery"], "outputs": ["load"]},
            {"id": "grid_purchase", "name": "grid_purchase", "description": None, "inputs": ["grid"], "outputs": ["load"]},
            {"id": "load_consumption", "name": "load_consumption", "description": None, "inputs": ["load"], "outputs": []},
        ],
        "constraints": [
            {"id": "soc_limits", "name": "SOC limits", "expression": "SOC_min <= SOC <= SOC_max", "description": None, "variables": ["battery_soc_min", "battery_soc", "battery_soc_max"]}
        ],
        "objectives": [
            {"id": "minimize_operating_cost", "name": "operating_cost", "expression": "minimize operating_cost", "description": None, "direction": "minimize"}
        ],
    }


def load_demo_document() -> RawDocument:
    l1_document = FileMarkdownLoader().load(DEMO_MARKDOWN)
    return RawDocument.from_markdown_document(l1_document)


def build_demo_client() -> MockLLMClient:
    return MockLLMClient(
        responses=[
            json.dumps(_requirement_payload(), ensure_ascii=False),
            json.dumps(_knowledge_state_payload(), ensure_ascii=False),
        ]
    )


def run_demo() -> int:
    result = L2Orchestrator(build_demo_client()).run(load_demo_document())
    print(f"Status: {result.status}")
    print(f"Entities: {len(result.knowledge_state.entities)}")
    print(f"Attributes: {len(result.knowledge_state.attributes)}")
    print(f"States: {len(result.knowledge_state.states)}")
    print(f"Relations: {len(result.knowledge_state.relations)}")
    print(f"Processes: {len(result.knowledge_state.processes)}")
    print(f"Constraints: {len(result.knowledge_state.constraints)}")
    print(f"Objectives: {len(result.knowledge_state.objectives)}")
    print(result.knowledge_state.model_dump_json(indent=2))
    return 0 if result.status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(run_demo())