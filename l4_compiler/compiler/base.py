"""L4 compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from l3_sysml import SysMLModel
from l4_compiler.world_model_ir import SimulationSettings, WorldModel


class WorldModelCompiler(Protocol):
    def compile(
        self,
        sysml_model: SysMLModel | dict | str | Path,
        *,
        simulation: SimulationSettings | None = None,
    ) -> WorldModel:
        ...