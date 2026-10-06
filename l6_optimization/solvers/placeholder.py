"""A solver placeholder that does not claim a numeric optimum."""

from __future__ import annotations

from typing import Mapping

from l6_optimization.models import OptimizationProblem, OptimizationResult, SolverStatus


class PlaceholderSolver:
    @property
    def name(self) -> str:
        return "placeholder"

    def solve(
        self,
        problem: OptimizationProblem,
        *,
        context: Mapping[str, object] | None = None,
    ) -> OptimizationResult:
        return OptimizationResult(
            result_id=f"{problem.problem_id}-result",
            problem_id=problem.problem_id,
            status=SolverStatus.PLACEHOLDER,
            solver_name=self.name,
            feasible=None,
            objective_value=None,
            variable_values={},
            message="No optimization algorithm is implemented in Phase 0.",
            metadata={
                "status": "placeholder",
                "variable_count": len(problem.variables),
                "objective_count": len(problem.objectives),
                "constraint_count": len(problem.constraints),
                "has_context": bool(context),
            },
        )