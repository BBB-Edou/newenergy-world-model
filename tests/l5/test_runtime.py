from __future__ import annotations

from pathlib import Path

import pytest

from l2_modeling.scenario import ScenarioData, ScenarioSource
from l4_compiler.world_model_ir import SimulationSettings, WorldModel
from l5_world_model import FixedActionPolicy, SimulationConfig, SimulationResult, WorldModelRuntime
from l5_world_model.dynamics.battery import resolve_battery_parameters
from scenario_binding import ScenarioAlignment


ROOT = Path(__file__).resolve().parents[2]
WORLD_MODEL_PATH = ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
REQUIRED = ["wind_power", "pv_power", "load_power", "electricity_price"]


def _world_model() -> WorldModel:
    return WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))


def _scenario() -> ScenarioData:
    pv = [0, 0, 0, 0, 0, 0, 20, 50, 80, 100, 100, 80, 60, 40, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    return ScenarioData(
        scenario_id="scenario_24h",
        time=[f"{hour:02d}:00" for hour in range(24)],
        variables={
            "wind_power": [100.0] * 24,
            "pv_power": [float(value) for value in pv],
            "load_power": [150.0] * 24,
            "electricity_price": [0.35] * 24,
        },
        units={"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
        metadata={"time_step": "1h"},
        source=ScenarioSource(document="scenario_24h.json", table_id="table_01", page=1),
    )


def _binding():
    return ScenarioAlignment().align(_world_model(), _scenario())


def _config(steps: int = 24) -> SimulationConfig:
    return SimulationConfig(steps=steps, step_size=1.0, time_unit="h")


def test_24h_runtime_completes_24_steps() -> None:
    result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config()).run()
    assert result.status == "COMPLETED"
    assert len(result.step_metrics) == 24
    assert len(result.trace) == 25
    assert result.final_state.time == 24.0


def test_battery_soc_evolution_follows_charge_action() -> None:
    action_policy = FixedActionPolicy({"battery_charge": 20.0, "battery_discharge": 0.0})
    result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=1), action_policy=action_policy).run()
    assert result.initial_state.values["state-battery_soc"] == 50
    assert result.final_state.values["state-battery_soc"] == pytest.approx(59.5)


def test_power_balance_is_recorded() -> None:
    result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=1)).run()
    metrics = result.step_metrics[0]
    assert metrics.wind_power + metrics.pv_power + metrics.grid_import + metrics.battery_discharge == pytest.approx(metrics.load_power + metrics.battery_charge + metrics.curtailment)


def test_soc_boundary_violation_is_detected() -> None:
    action_policy = FixedActionPolicy({"battery_charge": 300.0, "battery_discharge": 0.0})
    result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=1), action_policy=action_policy).run()
    codes = {violation.code for violation in result.constraint_violations}
    assert "soc_bounds" in codes
    assert "charge_power_limit" in codes


def test_runtime_is_deterministic() -> None:
    action_policy = FixedActionPolicy({"battery_charge": 20.0, "battery_discharge": 0.0})
    first = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=4), action_policy=action_policy).run()
    second = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=4), action_policy=action_policy).run()
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_different_actions_produce_different_soc_trajectory() -> None:
    charge = FixedActionPolicy({"battery_charge": 20.0, "battery_discharge": 0.0})
    discharge = FixedActionPolicy({"battery_charge": 0.0, "battery_discharge": 20.0})
    charge_result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=2), action_policy=charge).run()
    discharge_result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=2), action_policy=discharge).run()
    assert charge_result.final_state.values["state-battery_soc"] != discharge_result.final_state.values["state-battery_soc"]


def test_runtime_uses_real_scenario_input_binding() -> None:
    binding = _binding()
    assert binding.status == "READY"
    result = WorldModelRuntime(world_model=_world_model(), binding=binding, config=_config(steps=1)).run()
    assert result.metadata["binding_status"] == "READY"
    assert result.inputs[0]["wind_power"] == 100.0

def test_simulation_result_json_roundtrip() -> None:
    result = WorldModelRuntime(world_model=_world_model(), binding=_binding(), config=_config(steps=2)).run()
    restored = SimulationResult.from_json(result.to_json())
    assert restored.final_state == result.final_state
    assert restored.step_metrics == result.step_metrics
    assert restored.events == result.events

def test_battery_efficiency_is_read_from_world_model_ir() -> None:
    parameters = resolve_battery_parameters(_world_model(), _config(steps=1))
    assert parameters.charge_efficiency == 0.95
    assert parameters.discharge_efficiency == 0.95