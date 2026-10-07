"""Run the 24h L6 CVXPY optimization demo and close the loop through L5.

Pipeline:

    WorldModelIR + ScenarioInputBinding
        -> CVXPYOptimizer
        -> Optimal ActionSequence
        -> L5 WorldModelRuntime
        -> SimulationResult
        -> OptimizationResult

Also reports a ZeroActionPolicy baseline for comparison.
"""

from __future__ import annotations

from pathlib import Path

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig, SimulationEngine, ZeroActionPolicy
from l6_optimization import CVXPYOptimizer
from scenario_binding import ScenarioAlignment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORLD_MODEL_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"
RESULT_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l6" / "optimization_result.json"


def _summarize(result) -> dict[str, object]:
    return {metric.name: metric.value for metric in result.metrics}


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

    time = contract.time_requirements
    config = SimulationConfig(steps=time.horizon, step_size=time.step_size, time_unit=time.time_unit)

    optimization = CVXPYOptimizer().solve(
        world_model_ir=world_model,
        scenario_binding=binding,
        scenario_data=scenario,
        simulation_config=config,
    )
    if optimization.simulation_result is None:
        print(f"Optimization did not produce a simulation result (status={optimization.status.value})")
        print(optimization.message)
        return 1

    baseline = SimulationEngine().run(world_model=world_model, binding=binding, config=config, action_policy=ZeroActionPolicy())

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(optimization.to_json() + "\n", encoding="utf-8")

    summary = _summarize(optimization.simulation_result)
    baseline_summary = _summarize(baseline)

    print("Optimization completed")
    print(f"Horizon: {time.horizon} {time.time_unit}")
    print(f"Solver: {optimization.solver_name}")
    print(f"Solver Status: {optimization.status.value}")
    print()
    print(f"Objective Value: {optimization.objective_value}")
    print(f"Total Cost: {summary.get('total_cost')}")
    print(f"Peak Grid Import: {summary.get('peak_grid_import')}")
    print(f"Final SOC: {summary.get('final_soc')}")
    print(f"Curtailment: {summary.get('curtailment')}")
    print()
    print(f"Constraint Violations: {summary.get('constraint_violation_count')}")
    print(f"L6 -> L5 consistency: {optimization.consistency_report.valid if optimization.consistency_report else None}")
    print()
    print("Baseline vs Optimization")
    print(f"  ZeroAction total cost: {baseline_summary.get('total_cost')}")
    print(f"  Optimal total cost:    {summary.get('total_cost')}")
    print()
    print("t   wind    pv      load    charge  discharge  grid    soc     curtail  cost")
    for metrics in optimization.simulation_result.step_metrics:
        print(
            f"{metrics.step_index:<3}"
            f"{metrics.wind_power:<8.1f}"
            f"{metrics.pv_power:<8.1f}"
            f"{metrics.load_power:<8.1f}"
            f"{metrics.battery_charge:<8.1f}"
            f"{metrics.battery_discharge:<11.1f}"
            f"{metrics.grid_import:<8.1f}"
            f"{metrics.battery_soc:<8.2f}"
            f"{metrics.curtailment:<9.1f}"
            f"{metrics.cost if metrics.cost is not None else 0.0:.3f}"
        )
    print()
    print(f"Result: {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
