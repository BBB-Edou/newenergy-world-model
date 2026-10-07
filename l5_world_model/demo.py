"""Run the 24h Wind-PV-Battery-Grid-Load deterministic simulation demo."""

from __future__ import annotations

from pathlib import Path

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import Action, OpenLoopActionSequence, SimulationConfig, SimulationEngine
from scenario_binding import ScenarioAlignment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORLD_MODEL_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"
RESULT_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l5" / "simulation_result.json"


def run_demo() -> int:
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    contract = world_model.scenario_input_contract
    if contract is None:
        print("WorldModelIR has no ScenarioInputContract")
        return 1
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    binding = ScenarioAlignment().align(world_model, scenario)
    if binding.status != "READY":
        print(f"Binding status: {binding.status}")
        print(binding.model_dump_json(indent=2))
        return 1

    actions = [
        Action(action_id=f"dispatch-{step}", name="fixed_demo_dispatch", values={"battery_charge": 20.0 if step < 3 else 0.0, "battery_discharge": 20.0 if step in {18, 19} else 0.0})
        for step in range(contract.time_requirements.horizon)
    ]
    config = SimulationConfig(
        steps=contract.time_requirements.horizon,
        step_size=contract.time_requirements.step_size,
        time_unit=contract.time_requirements.time_unit,
    )
    result = SimulationEngine().run(world_model=world_model, binding=binding, config=config, action_policy=OpenLoopActionSequence(actions))
    RESULT_PATH.write_text(result.to_json() + "\n", encoding="utf-8")
    summary = {metric.name: metric.value for metric in result.metrics}
    print("Simulation completed")
    print(f"Horizon: {contract.time_requirements.horizon} {contract.time_requirements.time_unit}")
    print(f"Steps: {len(result.step_metrics)}")
    print(f"Total Cost: {summary['total_cost']}")
    print(f"Peak Grid Import: {summary['peak_grid_import']}")
    print(f"Final SOC: {summary['final_soc']}")
    print(f"Curtailment: {summary['curtailment']}")
    print(f"Constraint Violations: {summary['constraint_violation_count']}")
    print(f"Result: {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())