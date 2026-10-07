from __future__ import annotations

from l2_modeling.scenario import ScenarioData, ScenarioSource
from l4_compiler.world_model_ir import Entity, Interface, SimulationSettings, WorldModel, WorldModelMetadata
from scenario_binding import ScenarioAlignment


REQUIRED = ["wind_power", "pv_power", "load_power", "electricity_price"]


def _world_model(*, units=None, step_size=1.0, time_unit="h", required=REQUIRED, horizon=2) -> WorldModel:
    return WorldModel(
        metadata=WorldModelMetadata(
            ir_id="wm_001",
            name="Renewable World",
            required_inputs=required,
            input_units=units or {name: ("kW" if name != "electricity_price" else "CNY/kWh") for name in required},
            simulation=SimulationSettings(step_size=step_size, horizon=horizon, time_unit=time_unit),
        )
    )


def _scenario(*, variables=None, units=None, time_step="1h", aliases=None) -> ScenarioData:
    variables = variables or {
        "wind_power": [120, 110],
        "pv_power": [0, 0],
        "load_power": [300, 280],
        "electricity_price": [0.35, 0.35],
    }
    units = units or {"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"}
    metadata = {"time_step": time_step}
    if aliases is not None:
        metadata["variable_aliases"] = aliases
    return ScenarioData(
        scenario_id="scenario_001",
        time=["00:00", "01:00"],
        variables=variables,
        units=units,
        metadata=metadata,
        source=ScenarioSource(document="case.pdf", table_id="table_01", page=1),
    )


def test_exact_match_is_ready() -> None:
    binding = ScenarioAlignment().align(_world_model(), _scenario())
    assert binding.status == "READY"
    assert binding.variable_mapping == {name: name for name in REQUIRED}
    assert binding.validation_summary.missing_inputs == []


def test_missing_input_needs_user_input() -> None:
    variables = {name: [120, 110] for name in REQUIRED if name != "electricity_price"}
    units = {name: "kW" for name in variables}
    binding = ScenarioAlignment().align(_world_model(), _scenario(variables=variables, units=units))
    assert binding.status == "NEED_INPUT"
    assert "electricity_price" in binding.validation_summary.missing_inputs


def test_known_unit_conversion_is_ready_and_recorded() -> None:
    units = {"wind_power": "MW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"}
    binding = ScenarioAlignment().align(_world_model(), _scenario(units=units))
    assert binding.status == "READY"
    assert binding.unit_mapping["wind_power"].conversion == "×1000"
    assert binding.unit_mapping["wind_power"].factor == 1000


def test_unknown_unit_needs_input() -> None:
    units = {"wind_power": "unknown", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"}
    binding = ScenarioAlignment().align(_world_model(), _scenario(units=units))
    assert binding.status == "NEED_INPUT"
    assert binding.validation_summary.unit_mismatches


def test_matching_time_step_is_ready() -> None:
    binding = ScenarioAlignment().align(_world_model(), _scenario(time_step="1h"))
    assert binding.status == "READY"
    assert binding.validation_summary.time_mismatch is False
    assert binding.time_mapping.source_step == "1h"
    assert binding.time_mapping.target_step == "1h"


def test_time_step_mismatch_is_invalid_without_resampling() -> None:
    scenario = ScenarioData(
        scenario_id="scenario_001",
        time=["00:00", "00:15"],
        variables={name: [1, 2] for name in REQUIRED},
        units={name: ("kW" if name != "electricity_price" else "CNY/kWh") for name in REQUIRED},
        metadata={"time_step": "15min"},
        source=ScenarioSource(document="case.pdf", table_id="table_01", page=1),
    )
    binding = ScenarioAlignment().align(_world_model(), scenario)
    assert binding.status == "INVALID"
    assert binding.validation_summary.time_mismatch


def test_ambiguous_variable_name_needs_input() -> None:
    variables = {"wind_power": [120, 110], "solar_output": [10, 20], "load_power": [300, 280], "electricity_price": [0.35, 0.35]}
    units = {"wind_power": "kW", "solar_output": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"}
    binding = ScenarioAlignment().align(_world_model(), _scenario(variables=variables, units=units))
    assert binding.status == "NEED_INPUT"
    assert "pv_power" in binding.validation_summary.missing_inputs


def test_explicit_alias_is_used_without_guessing() -> None:
    variables = {"wind_power": [120, 110], "solar_output": [10, 20], "load_power": [300, 280], "electricity_price": [0.35, 0.35]}
    units = {"wind_power": "kW", "solar_output": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"}
    binding = ScenarioAlignment().align(
        _world_model(),
        _scenario(variables=variables, units=units, aliases={"pv_power": "solar_output"}),
    )
    assert binding.status == "READY"
    assert binding.variable_mapping["pv_power"] == "solar_output"


def test_alignment_is_deterministic() -> None:
    first = ScenarioAlignment().align(_world_model(), _scenario())
    second = ScenarioAlignment().align(_world_model(), _scenario())
    assert first == second

def test_interface_variable_ids_supply_required_inputs_when_metadata_list_is_empty() -> None:
    model = WorldModel(
        metadata=WorldModelMetadata(
            ir_id="wm-interface",
            name="Interface World",
            input_units={name: ("kW" if name != "electricity_price" else "CNY/kWh") for name in REQUIRED},
            simulation=SimulationSettings(step_size=1.0, horizon=2, time_unit="h"),
        ),
        entities=[Entity(id="entity-runtime", name="Runtime", entity_type="system")],
        interfaces=[
            Interface(
                id="interface-inputs",
                name="runtime inputs",
                source="entity-runtime",
                target="entity-runtime",
                variable_ids=REQUIRED,
            )
        ],
    )
    binding = ScenarioAlignment().align(model, _scenario())
    assert binding.status == "READY"
    assert set(binding.variable_mapping) == set(REQUIRED)


def test_model_without_input_contract_needs_input() -> None:
    binding = ScenarioAlignment().align(WorldModel(metadata=WorldModelMetadata(ir_id="wm-empty", name="Empty")), _scenario())
    assert binding.status == "NEED_INPUT"
    assert binding.validation_summary.missing_inputs

def test_compiler_generated_scenario_input_contract_is_used_by_binding() -> None:
    from pathlib import Path as FilePath
    from l3_sysml import SysMLModel
    from l4_compiler import ModelCompiler

    root = FilePath(__file__).resolve().parents[2]
    sysml = SysMLModel.model_validate_json((root / "examples" / "renewable_energy" / "l3" / "demo_sysml.json").read_text(encoding="utf-8"))
    world_model = ModelCompiler().compile(sysml, simulation=SimulationSettings(step_size=1.0, horizon=24, time_unit="h"))
    pv = [0] * 6 + [20, 50, 80, 100, 100, 80, 60, 40, 20] + [0] * 9
    scenario = ScenarioData(
        scenario_id="contract-scenario",
        time=[f"{hour:02d}:00" for hour in range(24)],
        variables={"wind_power": [100.0] * 24, "pv_power": [float(v) for v in pv], "load_power": [150.0] * 24, "electricity_price": [0.35] * 24},
        units={"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
        metadata={"time_step": "1h"},
        source=ScenarioSource(document="scenario_24h.json", table_id="table_01", page=1),
    )
    binding = ScenarioAlignment().align(world_model, scenario)
    assert binding.status == "READY"
    assert world_model.scenario_input_contract is not None
    assert {item.name for item in world_model.scenario_input_contract.inputs} == set(REQUIRED)
    assert binding.variable_mapping == {name: name for name in REQUIRED}


def test_insufficient_scenario_horizon_needs_input() -> None:
    binding = ScenarioAlignment().align(_world_model(horizon=3), _scenario())
    assert binding.status == "NEED_INPUT"
    assert any("insufficient scenario horizon" in item for item in binding.validation_summary.missing_inputs)


def test_non_numeric_contract_input_is_invalid() -> None:
    variables = {"wind_power": ["bad", 110], "pv_power": [0, 0], "load_power": [300, 280], "electricity_price": [0.35, 0.35]}
    binding = ScenarioAlignment().align(_world_model(), _scenario(variables=variables))
    assert binding.status == "INVALID"