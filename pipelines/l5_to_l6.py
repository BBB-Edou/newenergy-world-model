"""L5 -> L6 pipeline stage."""

from __future__ import annotations

from l5_world_model import SimulationResult
from l6_optimization import (
    OptimizationProblem,
    OptimizationResult,
    PlaceholderSolver,
    Solver,
    build_optimization_problem,
)


def run_l5_to_l6(simulation_result: SimulationResult, *, solver: Solver | None = None) -> tuple[OptimizationProblem, OptimizationResult]:
    problem = build_optimization_problem(simulation_result)
    result = (solver or PlaceholderSolver()).solve(problem)
    return problem, result