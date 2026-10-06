"""L6 optimization contracts independent of a specific solver."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from common import Metadata


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


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionVariable:
    variable_id: str
    name: str
    variable_type: DecisionVariableType = DecisionVariableType.CONTINUOUS
    lower_bound: float | int | None = None
    upper_bound: float | int | None = None
    unit: str | None = None
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class OptimizationObjective:
    objective_id: str
    name: str
    sense: ObjectiveSense = ObjectiveSense.UNDECIDED
    expression: str | None = None
    variable_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class OptimizationConstraint:
    constraint_id: str
    name: str
    sense: ConstraintSense = ConstraintSense.EXPRESSION
    expression: str | None = None
    variable_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class OptimizationProblem:
    problem_id: str
    name: str
    variables: tuple[DecisionVariable, ...] = ()
    objectives: tuple[OptimizationObjective, ...] = ()
    constraints: tuple[OptimizationConstraint, ...] = ()
    parameters: Metadata = field(default_factory=dict)
    source_simulation_id: str | None = None
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class OptimizationResult:
    result_id: str
    problem_id: str
    status: SolverStatus
    solver_name: str
    feasible: bool | None = None
    objective_value: float | None = None
    variable_values: Metadata = field(default_factory=dict)
    message: str | None = None
    metadata: Metadata = field(default_factory=dict)