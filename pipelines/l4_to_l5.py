"""L4 -> L5 pipeline stage."""

from __future__ import annotations

from l4_compiler import WorldModelIR
from l5_world_model import ExecutableWorldModel, SimulationConfig, build_world_model


def run_l4_to_l5(world_model_ir: WorldModelIR, *, config: SimulationConfig | None = None) -> ExecutableWorldModel:
    return build_world_model(world_model_ir, config=config)