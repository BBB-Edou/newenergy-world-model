"""Typed L6 optimization contracts."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from l5_world_model.models import Action, SimulationResult


class L6SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DecisionVariableType(str, Enum):
    CONTINUOUS = "continuous"
    INTEGER = "integer"
    BINARY = "binary"


class ObjectiveSense(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    UNDECIDED = "undecided"


class ConstraintSense(str, Enum):
    LESS_EQUAL = "less_equal"
    EQUAL = "equal"
    GREATER_EQUAL = "greater_equal"
    EXPRESSION = "expression"


class SolverStatus(str, Enum):
    PLACEHOLDER = "placeholder"
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    ERROR = "error"


class OptimizationConfig(L6SchemaModel):
    solver_name: str = "CLARABEL"
    tolerance: float = 1e-5
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionVariable(L6SchemaModel):
    variable_id: str
    name: str
    variable_type: DecisionVariableType = DecisionVariableType.CONTINUOUS
    lower_bound: float | int | None = None
    upper_bound: float | int | None = None
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationObjective(L6SchemaModel):
    objective_id: str
    name: str
    sense: ObjectiveSense = ObjectiveSense.UNDECIDED
    expression: str | None = None
    variable_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationConstraint(L6SchemaModel):
    constraint_id: str
    name: str
    sense: ConstraintSense = ConstraintSense.EXPRESSION
    expression: str | None = None
    variable_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationProblem(L6SchemaModel):
    problem_id: str
    name: str
    variables: list[DecisionVariable] = Field(default_factory=list)
    objectives: list[OptimizationObjective] = Field(default_factory=list)
    constraints: list[OptimizationConstraint] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    source_simulation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstraintSummary(L6SchemaModel):
    total: int
    satisfied: int
    violated: int
    details: list[str] = Field(default_factory=list)


class SolverInfo(L6SchemaModel):
    solver_name: str
    status: SolverStatus
    message: str | None = None
    iterations: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActionSequence(L6SchemaModel):
    actions: list[Action] = Field(default_factory=list)


class ConsistencyReport(L6SchemaModel):
    valid: bool
    tolerance: float
    max_abs_error: dict[str, float] = Field(default_factory=dict)


class OptimizationResult(L6SchemaModel):
    result_id: str
    problem_id: str
    status: SolverStatus
    solver_name: str
    feasible: bool | None = None
    objective_value: float | None = None
    variable_values: dict[str, Any] = Field(default_factory=dict)
    decision_variables: dict[str, list[float]] = Field(default_factory=dict)
    action_sequence: list[Action] = Field(default_factory=list)
    constraint_summary: ConstraintSummary | None = None
    solver_info: SolverInfo | None = None
    simulation_result: SimulationResult | None = None
    consistency_report: ConsistencyReport | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, payload: str) -> "OptimizationResult":
        return cls.model_validate_json(payload)


class WhatIfScenarioResult(L6SchemaModel):
    scenario_name: str
    optimization_result: OptimizationResult
    total_cost: float | None = None
    renewable_utilization: float | None = None
    curtailment: float | None = None
    peak_grid_import: float | None = None
    final_soc: float | None = None


class WhatIfResult(L6SchemaModel):
    scenarios: list[WhatIfScenarioResult] = Field(default_factory=list)
    comparison: dict[str, list[float | None]] = Field(default_factory=dict)