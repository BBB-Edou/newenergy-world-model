"""Run deterministic alignment on the existing renewable-energy demo artefacts."""

from __future__ import annotations

from pathlib import Path

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from scenario_binding import ScenarioAlignment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORLD_MODEL_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"
OUTPUT_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "scenario_data" / "scenario_input_binding.json"


def run_demo() -> int:
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    binding = ScenarioAlignment().align(world_model, scenario)
    OUTPUT_PATH.write_text(binding.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Binding status: {binding.status}")
    print(f"Variable mappings: {binding.variable_mapping}")
    print(f"Time mapping: {binding.time_mapping.model_dump()}")
    print(f"Output: {OUTPUT_PATH}")
    return 0 if binding.status == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(run_demo())