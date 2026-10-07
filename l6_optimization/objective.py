"""Objective construction for the L6 MVP."""

from __future__ import annotations

import cvxpy as cp

from l6_optimization.variables import OptimizationVariables


def build_total_cost_objective(variables: OptimizationVariables, prices: list[float], delta_hours: float) -> cp.Expression:
    if len(prices) != variables.horizon:
        raise ValueError("price series length must match optimization horizon")
    return cp.sum(cp.multiply(prices, variables.grid_import) * delta_hours)