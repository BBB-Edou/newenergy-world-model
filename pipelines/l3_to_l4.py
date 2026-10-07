"""L3 -> L4 pipeline stage."""

from __future__ import annotations

from l3_sysml import SysMLModel
from l4_compiler import ModelCompiler, WorldModel
from l4_compiler.world_model_ir import SimulationSettings


def run_l3_to_l4(sysml_model: SysMLModel, *, simulation: SimulationSettings | None = None) -> WorldModel:
    return ModelCompiler().compile(sysml_model, simulation=simulation)