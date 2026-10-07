"""Executable world model contract consumed by L6 and runtime adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from l4_compiler.world_model_ir import WorldModel
from l5_world_model.models import Action, MetricValue, SimulationConfig, SimulationResult, WorldState


class ExecutableWorldModel(ABC):
    def __init__(self, ir: WorldModel, *, config: SimulationConfig | None = None) -> None:
        self.ir = ir
        self.config = config or SimulationConfig()
        self._state: WorldState | None = None

    @property
    def model_id(self) -> str:
        return self.ir.metadata.ir_id

    @abstractmethod
    def initialize(self) -> WorldState:
        ...

    @abstractmethod
    def step(self) -> WorldState:
        ...

    @abstractmethod
    def run(self) -> SimulationResult:
        ...

    @abstractmethod
    def get_state(self) -> WorldState:
        ...

    @abstractmethod
    def apply_action(self, action: Action) -> None:
        ...

    @abstractmethod
    def calculate_metrics(self) -> tuple[MetricValue, ...]:
        ...