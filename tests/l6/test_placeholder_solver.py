from __future__ import annotations

import unittest

from l6_optimization import OptimizationProblem, PlaceholderSolver, SolverStatus


class PlaceholderSolverTests(unittest.TestCase):
    def test_placeholder_solver_does_not_claim_an_optimum(self) -> None:
        problem = OptimizationProblem(problem_id="problem-1", name="Placeholder")

        result = PlaceholderSolver().solve(problem)

        self.assertIs(result.status, SolverStatus.PLACEHOLDER)
        self.assertIsNone(result.objective_value)
        self.assertIsNone(result.feasible)


if __name__ == "__main__":
    unittest.main()