"""Typed runtime models for the L5 world model simulation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class L5SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SimulationConfig(L5SchemaModel):
    steps: int = 1
    step_size: float = 1.0
    time_unit: str = "h"
    start_time: float = 0.0
    charge_efficiency: float | None = None
    discharge_efficiency: float | None = None
    seed: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_config(self) -> "SimulationConfig":
        if self.steps < 0:
            raise ValueError("steps must be non-negative")
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")
        for name, value in (("charge_efficiency", self.charge_efficiency), ("discharge_efficiency", self.discharge_efficiency)):
            if value is not None and not 0 < value <= 1:
                raise ValueError(f"{name} must be in (0, 1]")
        return self


class WorldState(L5SchemaModel):
    time: float = 0.0
    step_index: int = 0
    values: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class Action(L5SchemaModel):
    action_id: str
    name: str
    target_id: str | None = None
    values: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetricValue(L5SchemaModel):
    name: str
    value: Any
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstraintViolation(L5SchemaModel):
    code: str
    message: str
    time: float
    step_index: int
    severity: Literal["warning", "error"] = "error"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstraintEvaluation(L5SchemaModel):
    valid: bool
    violations: list[ConstraintViolation] = Field(default_factory=list)
    checked_constraints: list[str] = Field(default_factory=list)


class SimulationEvent(L5SchemaModel):
    event_id: str
    event_type: Literal["SimulationStart", "SimulationEnd", "ConstraintViolation", "BatterySOCBoundary", "GridLimitExceeded"]
    time: float
    step_index: int
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class StepMetrics(L5SchemaModel):
    step_index: int
    timestamp: str
    wind_power: float
    pv_power: float
    load_power: float
    battery_soc: float
    battery_charge: float
    battery_discharge: float
    grid_import: float
    curtailment: float
    cost: float | None = None


class SimulationTrace(L5SchemaModel):
    step_index: int
    state: WorldState
    actions: list[Action] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    events: list[SimulationEvent] = Field(default_factory=list)
    constraint_violations: list[ConstraintViolation] = Field(default_factory=list)
    metrics: StepMetrics | None = None


class SimulationStepRecord(L5SchemaModel):
    step_index: int
    time: float
    timestamp: str
    state_before: WorldState
    state_after: WorldState
    inputs: dict[str, float]
    action: Action
    constraint_evaluation: ConstraintEvaluation
    events: list[SimulationEvent] = Field(default_factory=list)
    metrics: StepMetrics


class SimulationResult(L5SchemaModel):
    simulation_id: str
    model_id: str
    status: Literal["COMPLETED", "FAILED"] = "COMPLETED"
    metadata: dict[str, Any] = Field(default_factory=dict)
    initial_state: WorldState
    final_state: WorldState
    states: list[WorldState] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    inputs: list[dict[str, float]] = Field(default_factory=list)
    events: list[SimulationEvent] = Field(default_factory=list)
    constraint_violations: list[ConstraintViolation] = Field(default_factory=list)
    metrics: list[MetricValue] = Field(default_factory=list)
    step_metrics: list[StepMetrics] = Field(default_factory=list)
    steps: list[SimulationStepRecord] = Field(default_factory=list)
    trace: list[SimulationTrace] = Field(default_factory=list)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, payload: str) -> "SimulationResult":
        return cls.model_validate_json(payload)