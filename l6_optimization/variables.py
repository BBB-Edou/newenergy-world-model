"""CVXPY decision-variable construction for the L6 MVP."""

from __future__ import annotations

from dataclasses import dataclass

import cvxpy as cp


@dataclass(slots=True)
class OptimizationVariables:
    horizon: int
    charge: cp.Variable
    discharge: cp.Variable
    grid_import: cp.Variable
    curtailment: cp.Variable
    soc: cp.Variable


def build_variables(horizon: int) -> OptimizationVariables:
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    return OptimizationVariables(
        horizon=horizon,
        charge=cp.Variable(horizon, nonneg=True, name="battery_charge"),
        discharge=cp.Variable(horizon, nonneg=True, name="battery_discharge"),
        grid_import=cp.Variable(horizon, nonneg=True, name="grid_import"),
        curtailment=cp.Variable(horizon, nonneg=True, name="curtailment"),
        soc=cp.Variable(horizon + 1, name="battery_soc"),
    )