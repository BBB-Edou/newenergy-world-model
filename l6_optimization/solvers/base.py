"""Solver boundary for CVXPY, Pyomo, MPC, RL or other adapters."""

from __future__ import annotations

from typing import Mapping, Protocol

from l6_optimization.models import OptimizationProblem, OptimizationResult


class Solver(Protocol):
    @property
    def name(self) -> str:
        ...

    def solve(
        self,
        problem: OptimizationProblem,
        *,
        context: Mapping[str, object] | None = None,
    ) -> OptimizationResult:
        """Solve a model-neutral optimization problem."""
        ...