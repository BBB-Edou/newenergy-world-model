from __future__ import annotations

from l2_modeling import KnowledgeState, MockLLMClient
from l3_sysml import KnowledgeStateToSysMLMapper, PlantUMLGenerator, SysMLAgent


def _demo_state() -> KnowledgeState:
    return KnowledgeState.model_validate({
        "schema_version": "1.0",
        "entities": [
            {"id": "wind", "name": "Wind", "entity_type": "renewable_source"},
            {"id": "pv", "name": "PV", "entity_type": "renewable_source"},
            {"id": "battery", "name": "Battery", "entity_type": "storage"},
            {"id": "grid", "name": "Grid", "entity_type": "grid_connection"},
            {"id": "load", "name": "Load", "entity_type": "demand"},
        ],
        "attributes": [
            {"id": "wind_power", "entity_id": "wind", "name": "rated_power", "value": 100, "unit": "kW"},
            {"id": "pv_power", "entity_id": "pv", "name": "rated_power", "value": 80, "unit": "kW"},
            {"id": "battery_capacity", "entity_id": "battery", "name": "capacity", "value": 200, "unit": "kWh"},
            {"id": "grid_power", "entity_id": "grid", "name": "max_import_power", "value": 150, "unit": "kW"},
            {"id": "load_demand", "entity_id": "load", "name": "demand", "value": 120, "unit": "kW"},
        ],
        "states": [{"id": "battery_soc", "entity_id": "battery", "name": "SOC", "value": 50, "unit": "%"}],
        "relations": [
            {"id": "wind_load", "relation_type": "supplies", "source_entity_id": "wind", "target_entity_id": "load"},
            {"id": "pv_load", "relation_type": "supplies", "source_entity_id": "pv", "target_entity_id": "load"},
            {"id": "battery_load", "relation_type": "supplies", "source_entity_id": "battery", "target_entity_id": "load"},
            {"id": "grid_load", "relation_type": "supplies", "source_entity_id": "grid", "target_entity_id": "load"},
        ],
        "processes": [{"id": "generation", "name": "generation", "inputs": ["wind", "pv"], "outputs": ["load"]}],
        "constraints": [{"id": "soc_limits", "name": "SOC limits", "expression": "SOC_min <= SOC <= SOC_max", "variables": ["battery_soc"]}],
        "objectives": [{"id": "cost", "name": "operating_cost", "expression": "minimize operating_cost", "direction": "minimize"}],
    })


def test_renewable_energy_end_to_end_with_shared_client() -> None:
    state = _demo_state()
    expected = KnowledgeStateToSysMLMapper().map(state)
    client = MockLLMClient(responses=[expected.model_dump_json()])

    model = SysMLAgent(client).run(state)
    plantuml = PlantUMLGenerator().generate(model)

    assert len(model.bdd.blocks) == 5
    assert len(model.ibd.connectors) == 4
    assert len(model.parametric.equations) == 2
    assert "@startuml bdd" in plantuml
    assert "Battery" in plantuml