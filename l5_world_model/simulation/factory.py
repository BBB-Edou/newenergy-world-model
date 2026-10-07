"""Factory boundary for replacing the Phase 0 executable model."""

from __future__ import annotations

from l4_compiler.world_model_ir import WorldModel
from l5_world_model.models import SimulationConfig
from l5_world_model.simulation.placeholder import PlaceholderWorldModel


def build_world_model(ir: WorldModel, *, config: SimulationConfig | None = None) -> PlaceholderWorldModel:
    return PlaceholderWorldModel(ir, config=config)