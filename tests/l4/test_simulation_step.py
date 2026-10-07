from __future__ import annotations

import pytest
from pydantic import ValidationError

from l3_sysml import SysMLModel
from l4_compiler import ModelCompiler
from l4_compiler.exporters import export_world_model_json
from l4_compiler.world_model_ir import SimulationSettings, WorldModel


def test_compiler_persists_explicit_timestep_and_horizon() -> None:
    settings = SimulationSettings(step_size=0.25, horizon=8, time_unit="hour")
    world_model = ModelCompiler().compile(SysMLModel(), simulation=settings)

    assert world_model.metadata.simulation.step_size == 0.25
    assert world_model.metadata.simulation.horizon == 8
    assert world_model.metadata.simulation.time_unit == "hour"


def test_timestep_survives_json_roundtrip() -> None:
    settings = SimulationSettings(step_size=0.5, horizon=4, time_unit="minute")
    world_model = ModelCompiler().compile(SysMLModel(), simulation=settings)

    restored = WorldModel.model_validate_json(export_world_model_json(world_model))

    assert restored.metadata.simulation == settings


@pytest.mark.parametrize("step_size", [0.0, -1.0])
def test_timestep_must_be_positive(step_size: float) -> None:
    with pytest.raises(ValidationError):
        SimulationSettings(step_size=step_size)


def test_horizon_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        SimulationSettings(horizon=-1)