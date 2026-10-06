"""Executable world model contract consumed by L6 and runtime adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from l4_compiler.world_model_ir import WorldModelIR
from l5_world_model.models import (
    Action,
    MetricValue,
    SimulationConfig,
    SimulationResult,
    WorldState,
)


class ExecutableWorldModel(ABC):
    """Stable L5 contract independent of any SysML tool."""

    def __init__(self, ir: WorldModelIR, *, config: SimulationConfig | None = None) -> None:
        self.ir = ir
        self.config = config or SimulationConfig()
        self._state: WorldState | None = None

    @property
    def model_id(self) -> str:
        return self.ir.ir_id

    @abstractmethod
    def initialize(self) -> WorldState:
        """Initialize and store the model state."""

    @abstractmethod
    def step(self) -> WorldState:
        """Advance the model by one simulation step."""

    @abstractmethod
    def run(self) -> SimulationResult:
        """Run the configured horizon and return a simulation result."""

    @abstractmethod
    def get_state(self) -> WorldState:
        """Return the current state."""

    @abstractmethod
    def apply_action(self, action: Action) -> None:
        """Apply or queue an external action using a model-neutral contract."""

    @abstractmethod
    def calculate_metrics(self) -> tuple[MetricValue, ...]:
        """Calculate metrics from the current simulation artifacts."""