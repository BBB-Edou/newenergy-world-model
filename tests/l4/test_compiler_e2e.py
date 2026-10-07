from __future__ import annotations

from pathlib import Path

from l3_sysml import SysMLModel
from l4_compiler import ModelCompiler, validate_world_model
from l4_compiler.exporters import export_world_model_json
from l4_compiler.world_model_ir import SimulationSettings


ROOT = Path(__file__).resolve().parents[2]
DEMO_SYSML = ROOT / "examples" / "renewable_energy" / "l3" / "demo_sysml.json"


def test_renewable_energy_compiler_end_to_end() -> None:
    sysml_model = SysMLModel.model_validate_json(DEMO_SYSML.read_text(encoding="utf-8"))
    world_model = ModelCompiler().compile(sysml_model, simulation=SimulationSettings(step_size=1.0, horizon=24, time_unit="h"))

    assert validate_world_model(world_model).valid
    assert {entity.name for entity in world_model.entities} == {"Wind", "PV", "Battery", "Grid", "Load"}
    assert len(world_model.attributes) == 12
    assert len(world_model.states) == 1
    assert len(world_model.behaviors) == 5
    assert len(world_model.equations) == 2
    assert len(world_model.constraints) == 1
    assert len(world_model.objectives) == 1
    assert len(world_model.interfaces) == 4
    assert all(item.trace for item in world_model.entities + world_model.attributes + world_model.interfaces)
    assert world_model.scenario_input_contract is not None
    assert {item.name for item in world_model.scenario_input_contract.inputs} == {"wind_power", "pv_power", "load_power", "electricity_price"}
    assert world_model.scenario_input_contract.time_requirements.horizon == 24


def test_compiler_is_deterministic() -> None:
    sysml_model = SysMLModel.model_validate_json(DEMO_SYSML.read_text(encoding="utf-8"))
    first = export_world_model_json(ModelCompiler().compile(sysml_model, simulation=SimulationSettings(step_size=1.0, horizon=24, time_unit="h")))
    second = export_world_model_json(ModelCompiler().compile(sysml_model, simulation=SimulationSettings(step_size=1.0, horizon=24, time_unit="h")))
    assert first == second

def test_battery_capacity_traces_to_sysml_and_knowledge_state() -> None:
    sysml_model = SysMLModel.model_validate_json(DEMO_SYSML.read_text(encoding="utf-8"))
    world_model = ModelCompiler().compile(sysml_model, simulation=SimulationSettings(step_size=1.0, horizon=24, time_unit="h"))

    battery = next(entity for entity in world_model.entities if entity.name == "Battery")
    capacity = next(
        attribute
        for attribute in world_model.attributes
        if attribute.owner == battery.id and attribute.name == "capacity"
    )
    trace_tuples = {
        (trace.source_type, trace.source_view, trace.source_id, trace.source_parent_id)
        for trace in capacity.trace
    }

    assert capacity.id == "attribute-battery_capacity"
    assert trace_tuples == {
        ("sysml", "BDD", "battery_capacity", "block-battery"),
        ("knowledge_state", "Attribute", "battery_capacity", "battery"),
    }