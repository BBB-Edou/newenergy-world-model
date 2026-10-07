from __future__ import annotations

from pathlib import Path

import pytest

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig, SimulationEngine, ZeroActionPolicy
from l6_optimization import CVXPYOptimizer, SolverStatus
from scenario_binding import ScenarioAlignment


ROOT = Path(__file__).resolve().parents[2]
WORLD_MODEL_PATH = ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"


def _inputs():
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    binding = ScenarioAlignment().align(world_model, scenario)
    config = SimulationConfig(steps=24, step_size=1.0, time_unit="h")
    return world_model, scenario, binding, config


@pytest.fixture(scope="module")
def optimized_result():
    world_model, _, binding, config = _inputs()
    return CVXPYOptimizer().solve(world_model_ir=world_model, scenario_binding=binding, simulation_config=config)


def test_24h_optimization_returns_optimal(optimized_result) -> None:
    assert optimized_result.status == SolverStatus.OPTIMAL
    assert optimized_result.feasible is True
    assert optimized_result.objective_value is not None


def test_action_sequence_can_be_consumed_by_l5(optimized_result) -> None:
    from l5_world_model import OpenLoopActionSequence

    policy = OpenLoopActionSequence(optimized_result.action_sequence)
    assert len(optimized_result.action_sequence) == 24
    assert policy.actions[0].action_id.startswith("optimal-")


def test_optimizer_executes_l5_simulation(optimized_result) -> None:
    assert optimized_result.simulation_result is not None
    assert optimized_result.simulation_result.status == "COMPLETED"
    assert len(optimized_result.simulation_result.step_metrics) == 24


def test_optimized_power_balance_holds(optimized_result) -> None:
    for metrics in optimized_result.simulation_result.step_metrics:
        assert metrics.wind_power + metrics.pv_power + metrics.grid_import + metrics.battery_discharge == pytest.approx(metrics.load_power + metrics.battery_charge + metrics.curtailment)


def test_optimized_soc_stays_inside_bounds(optimized_result) -> None:
    for metrics in optimized_result.simulation_result.step_metrics:
        assert 20.0 <= metrics.battery_soc <= 90.0


def test_optimized_battery_power_limits_hold(optimized_result) -> None:
    for action in optimized_result.action_sequence:
        assert 0.0 <= action.values["battery_charge"] <= 50.0
        assert 0.0 <= action.values["battery_discharge"] <= 50.0


def test_optimization_is_not_worse_than_zero_action_baseline(optimized_result) -> None:
    world_model, _, binding, config = _inputs()
    baseline = SimulationEngine().run(world_model=world_model, binding=binding, config=config, action_policy=ZeroActionPolicy())
    baseline_cost = next(metric.value for metric in baseline.metrics if metric.name == "total_cost")
    optimized_cost = next(metric.value for metric in optimized_result.simulation_result.metrics if metric.name == "total_cost")
    assert optimized_cost <= baseline_cost + 1e-4


def test_optimization_and_simulation_are_consistent(optimized_result) -> None:
    assert optimized_result.consistency_report is not None
    assert optimized_result.consistency_report.valid
    assert max(optimized_result.consistency_report.max_abs_error.values()) <= optimized_result.consistency_report.tolerance


def test_optimization_is_deterministic() -> None:
    world_model, _, binding, config = _inputs()
    first = CVXPYOptimizer().solve(world_model_ir=world_model, scenario_binding=binding, simulation_config=config)
    second = CVXPYOptimizer().solve(world_model_ir=world_model, scenario_binding=binding, simulation_config=config)
    assert first.objective_value == pytest.approx(second.objective_value, abs=1e-5)
    assert first.decision_variables == pytest.approx(second.decision_variables)