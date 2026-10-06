"""L3 -> L4 pipeline stage."""

from __future__ import annotations

from l3_sysml import SysMLModel
from l4_compiler import DefaultSysMLCompiler, WorldModelIR
from l4_compiler.world_model_ir import SimulationStepSpec


def run_l3_to_l4(sysml_model: SysMLModel, *, simulation: SimulationStepSpec | None = None) -> WorldModelIR:
    return DefaultSysMLCompiler().compile(sysml_model, simulation=simulation)