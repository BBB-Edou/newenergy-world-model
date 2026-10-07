"""Compile the renewable-energy SysML demo into World Model IR JSON."""

from __future__ import annotations

from pathlib import Path

from l3_sysml import SysMLModel
from l4_compiler import ModelCompiler, validate_world_model
from l4_compiler.world_model_ir import SimulationSettings
from l4_compiler.exporters import export_world_model_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYSML = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "demo_sysml.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"


def run_demo() -> int:
    sysml_model = SysMLModel.model_validate_json(DEFAULT_SYSML.read_text(encoding="utf-8"))
    world_model = ModelCompiler().compile(sysml_model, simulation=SimulationSettings(step_size=1.0, horizon=24, time_unit="h"))
    report = validate_world_model(world_model)
    export_world_model_json(world_model, DEFAULT_OUTPUT)
    print(f"IR valid: {report.valid}")
    print(f"Entities: {len(world_model.entities)}")
    print(f"Attributes: {len(world_model.attributes)}")
    print(f"States: {len(world_model.states)}")
    print(f"Behaviors: {len(world_model.behaviors)}")
    print(f"Events: {len(world_model.events)}")
    print(f"Equations: {len(world_model.equations)}")
    print(f"Constraints: {len(world_model.constraints)}")
    print(f"Objectives: {len(world_model.objectives)}")
    print(f"Interfaces: {len(world_model.interfaces)}")
    contract = world_model.scenario_input_contract
    print(f"Scenario inputs: {[item.name for item in contract.inputs] if contract else []}")
    print(f"World Model IR: {DEFAULT_OUTPUT}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(run_demo())