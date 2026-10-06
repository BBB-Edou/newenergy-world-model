from __future__ import annotations

from l2_modeling import KnowledgeState
from l3_sysml import KnowledgeStateToSysMLMapper, PlantUMLGenerator


def test_plantuml_generates_all_six_views() -> None:
    state = KnowledgeState(
        entities=[{"id": "battery", "name": "Battery", "entity_type": "storage"}],
        attributes=[{"id": "capacity", "entity_id": "battery", "name": "capacity", "value": 200, "unit": "kWh"}],
        states=[{"id": "soc", "entity_id": "battery", "name": "SOC", "value": 50, "unit": "%"}],
    )
    model = KnowledgeStateToSysMLMapper().map(state)

    source = PlantUMLGenerator().generate(model)

    assert "@startuml bdd" in source
    assert "@startuml ibd" in source
    assert "@startuml activity" in source
    assert "@startuml state" in source
    assert "@startuml requirements" in source
    assert "@startuml parametric" in source
    assert "Battery" in source