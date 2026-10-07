from __future__ import annotations

from pathlib import Path

import pytest

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig
from l6_optimization import CVXPYOptimizer, WhatIfRunner
from scenario_binding import ScenarioAlignment


ROOT = Path(__file__).resolve().parents[2]
WORLD_MODEL_PATH = ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"


def test_what_if_runs_multiple_scenarios_with_different_results() -> None:
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    binding = ScenarioAlignment().align(world_model, scenario)
    assert binding.status == "READY"
    config = SimulationConfig(steps=24, step_size=1.0, time_unit="h")
    variants = {
        "base": scenario,
        "high_price": WhatIfRunner.price_variant(scenario, scenario_id="high_price", multiplier=1.5),
        "low_renewable": WhatIfRunner.renewable_variant(scenario, scenario_id="low_renewable", wind_factor=0.8, pv_factor=0.8),
    }
    result = WhatIfRunner(CVXPYOptimizer()).run(world_model=world_model, scenario=scenario, simulation_config=config, variants=variants)

    assert [item.scenario_name for item in result.scenarios] == ["base", "high_price", "low_renewable"]
    assert all(item.total_cost is not None for item in result.scenarios)
    high_price = next(item for item in result.scenarios if item.scenario_name == "high_price")
    base = next(item for item in result.scenarios if item.scenario_name == "base")
    assert high_price.total_cost > base.total_cost


def test_what_if_battery_capacity_variants_are_optimized() -> None:
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    config = SimulationConfig(steps=24, step_size=1.0, time_unit="h")
    model_variants = {
        "battery_50": WhatIfRunner.capacity_variant(world_model, capacity_kwh=50.0),
        "battery_200": WhatIfRunner.capacity_variant(world_model, capacity_kwh=200.0),
    }
    result = WhatIfRunner(CVXPYOptimizer()).run(
        world_model=world_model,
        scenario=scenario,
        simulation_config=config,
        variants={"battery_50": scenario, "battery_200": scenario},
        world_model_variants=model_variants,
    )
    assert len(result.scenarios) == 2
    assert result.scenarios[0].final_soc is not None
    assert result.scenarios[1].final_soc is not None

def test_what_if_no_battery_variant_disables_battery() -> None:
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    config = SimulationConfig(steps=24, step_size=1.0, time_unit="h")
    model_variants = {"no_battery": WhatIfRunner.battery_power_variant(world_model, max_power_kw=0.0)}

    result = WhatIfRunner(CVXPYOptimizer()).run(
        world_model=world_model,
        scenario=scenario,
        simulation_config=config,
        variants={"no_battery": scenario},
        world_model_variants=model_variants,
    )

    no_battery = result.scenarios[0]
    assert no_battery.optimization_result.status.value == "optimal"
    assert no_battery.optimization_result.simulation_result is not None
    for metrics in no_battery.optimization_result.simulation_result.step_metrics:
        assert metrics.battery_charge == pytest.approx(0.0, abs=1e-6)
        assert metrics.battery_discharge == pytest.approx(0.0, abs=1e-6)
    assert no_battery.total_cost is not None
