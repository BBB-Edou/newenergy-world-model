from __future__ import annotations

from l2_modeling import KnowledgeState
from l3_sysml import KnowledgeStateToSysMLMapper


def _state() -> KnowledgeState:
    return KnowledgeState.model_validate(
        {
            "schema_version": "1.0",
            "entities": [
                {"id": "battery", "name": "Battery", "entity_type": "storage", "description": None},
                {"id": "load", "name": "Load", "entity_type": "demand", "description": None},
            ],
            "attributes": [
                {"id": "capacity", "entity_id": "battery", "name": "capacity", "value": 200, "unit": "kWh"},
                {"id": "demand", "entity_id": "load", "name": "demand", "value": 120, "unit": "kW"},
            ],
            "states": [
                {"id": "battery_soc", "entity_id": "battery", "name": "SOC", "value": 50, "unit": "%"}
            ],
            "relations": [
                {"id": "battery_to_load", "relation_type": "supplies", "source_entity_id": "battery", "target_entity_id": "load"}
            ],
            "processes": [
                {"id": "discharging", "name": "discharging", "inputs": ["battery"], "outputs": ["load"]}
            ],
            "constraints": [
                {"id": "soc_limits", "name": "SOC limits", "expression": "SOC_min <= SOC <= SOC_max", "variables": ["battery_soc"]}
            ],
            "objectives": [
                {"id": "min_cost", "name": "operating_cost", "expression": "minimize operating_cost", "direction": "minimize"}
            ],
        }
    )


def test_knowledge_state_maps_to_six_sysml_sections() -> None:
    model = KnowledgeStateToSysMLMapper().map(_state())

    assert len(model.bdd.blocks) == 2
    assert len(model.bdd.blocks[0].attributes) == 1
    assert len(model.ibd.connectors) == 1
    assert len(model.activity.actions) == 1
    assert len(model.state.machines) == 1
    assert len(model.requirements) == 2
    assert len(model.parametric.equations) == 2