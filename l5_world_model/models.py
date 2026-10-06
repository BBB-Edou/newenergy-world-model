"""Runtime state and result objects for L5."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from common import Metadata


@dataclass(frozen=True, slots=True, kw_only=True)
class WorldState:
    time: float = 0.0
    values: Metadata = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"time": self.time, "values": dict(self.values)}


@dataclass(frozen=True, slots=True, kw_only=True)
class Action:
    action_id: str
    name: str
    target_id: str | None = None
    values: Metadata = field(default_factory=dict)
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationConfig:
    steps: int = 1
    step_size: float = 1.0
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.steps < 0:
            raise ValueError("steps must be non-negative")
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class MetricValue:
    name: str
    value: Any
    unit: str | None = None
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationTrace:
    step_index: int
    state: WorldState
    actions: tuple[Action, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationResult:
    simulation_id: str
    model_id: str
    initial_state: WorldState
    final_state: WorldState
    trace: tuple[SimulationTrace, ...] = ()
    metrics: tuple[MetricValue, ...] = ()
    metadata: Metadata = field(default_factory=dict)