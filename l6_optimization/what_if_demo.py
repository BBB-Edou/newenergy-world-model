"""Run L6 what-if scenarios and compare the L6 -> L5 closed-loop outcomes.

Each scenario is re-optimized with CVXPY and then executed by the L5 runtime, so
every row in the comparison table is backed by a real simulation:

    Scenario -> CVXPY optimize -> L5 simulate -> metrics
"""

from __future__ import annotations

from pathlib import Path

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig
from l6_optimization import CVXPYOptimizer, WhatIfRunner
from scenario_binding import ScenarioAlignment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORLD_MODEL_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"
RESULT_PATH = PROJECT_ROOT / "examples" / "renewable_energy" / "l6" / "what_if_result.json"


def run_demo() -> int:
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    contract = world_model.scenario_input_contract
    if contract is None:
        print("WorldModelIR has no ScenarioInputContract")
        return 1

    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    if ScenarioAlignment().align(world_model, scenario).status != "READY":
        print("Base scenario is not READY against the WorldModelIR")
        return 1

    time = contract.time_requirements
    config = SimulationConfig(steps=time.horizon, step_size=time.step_size, time_unit=time.time_unit)

    variants = {
        "no_battery": scenario,
        "battery_050_kwh": scenario,
        "battery_100_kwh": scenario,
        "battery_200_kwh": scenario,
        "price_high_1.5x": WhatIfRunner.price_variant(scenario, scenario_id="price_high_1.5x", multiplier=1.5),
        "renewable_low_0.8x": WhatIfRunner.renewable_variant(scenario, scenario_id="renewable_low_0.8x", wind_factor=0.8, pv_factor=0.8),
    }
    world_model_variants = {
        "no_battery": WhatIfRunner.battery_power_variant(world_model, max_power_kw=0.0),
        "battery_050_kwh": WhatIfRunner.capacity_variant(world_model, capacity_kwh=50.0),
        "battery_100_kwh": WhatIfRunner.capacity_variant(world_model, capacity_kwh=100.0),
        "battery_200_kwh": WhatIfRunner.capacity_variant(world_model, capacity_kwh=200.0),
    }

    result = WhatIfRunner(CVXPYOptimizer()).run(
        world_model=world_model,
        scenario=scenario,
        simulation_config=config,
        variants=variants,
        world_model_variants=world_model_variants,
    )

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")

    header = f"{'Scenario':<22}{'Cost':>10}{'Curtailment':>14}{'Peak Grid':>12}{'Final SOC':>12}{'Renew.Util':>12}"
    print(header)
    print("-" * len(header))
    for item in result.scenarios:
        print(
            f"{item.scenario_name:<22}"
            f"{(item.total_cost if item.total_cost is not None else float('nan')):>10.2f}"
            f"{(item.curtailment if item.curtailment is not None else float('nan')):>14.2f}"
            f"{(item.peak_grid_import if item.peak_grid_import is not None else float('nan')):>12.2f}"
            f"{(item.final_soc if item.final_soc is not None else float('nan')):>12.2f}"
            f"{(item.renewable_utilization if item.renewable_utilization is not None else float('nan')):>12.4f}"
        )
    print()
    print(f"Scenarios: {len(result.scenarios)}")
    print(f"All scenarios solved and simulated: {all(item.optimization_result.simulation_result is not None for item in result.scenarios)}")
    print(f"Result: {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
