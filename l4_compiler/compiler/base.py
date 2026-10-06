"""L4 compiler boundary."""

from __future__ import annotations

from typing import Protocol

from l3_sysml import SysMLModel
from l4_compiler.world_model_ir import SimulationStepSpec, WorldModelIR


class WorldModelCompiler(Protocol):
    def compile(
        self,
        sysml_model: SysMLModel,
        *,
        simulation: SimulationStepSpec | None = None,
    ) -> WorldModelIR:
        """Compile a SysML model into an independent World Model IR."""
        ...


SysMLToWorldModelCompiler = WorldModelCompiler