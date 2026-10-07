"""L6: CVXPY-based scheduling optimization over the L5 world model."""

from .evaluator import OptimizationConsistencyError, compare_optimization_and_simulation
from .models import (
    ActionSequence,
    ConstraintSense,
    ConstraintSummary,
    ConsistencyReport,
    DecisionVariable,
    DecisionVariableType,
    ObjectiveSense,
    OptimizationConfig,
    OptimizationConstraint,
    OptimizationObjective,
    OptimizationProblem,
    OptimizationResult,
    SolverInfo,
    SolverStatus,
    WhatIfResult,
    WhatIfScenarioResult,
)
from .optimizer import CVXPYOptimizer, OptimizationModelError
from .problem import DISPATCH_VARIABLE_NAMES, build_dispatch_problem
from .scheduling.base import build_optimization_problem
from .solvers.base import Solver
from .solvers.placeholder import PlaceholderSolver
from .what_if.runner import WhatIfRunner

__all__ = [
    "ActionSequence",
    "CVXPYOptimizer",
    "DISPATCH_VARIABLE_NAMES",
    "ConstraintSense",
    "ConstraintSummary",
    "ConsistencyReport",
    "DecisionVariable",
    "DecisionVariableType",
    "ObjectiveSense",
    "OptimizationConfig",
    "OptimizationConsistencyError",
    "OptimizationConstraint",
    "OptimizationModelError",
    "OptimizationObjective",
    "OptimizationProblem",
    "OptimizationResult",
    "PlaceholderSolver",
    "Solver",
    "SolverInfo",
    "SolverStatus",
    "WhatIfResult",
    "WhatIfRunner",
    "WhatIfScenarioResult",
    "build_dispatch_problem",
    "build_optimization_problem",
    "compare_optimization_and_simulation",
]