"""Public optimization-problem description for the L6 dispatch MVP."""

from __future__ import annotations

from l5_world_model import SimulationConfig
from l6_optimization.models import (
    DecisionVariable,
    DecisionVariableType,
    ObjectiveSense,
    OptimizationObjective,
    OptimizationProblem,
)

DISPATCH_VARIABLE_NAMES = (
    "battery_charge",
    "battery_discharge",
    "grid_import",
    "curtailment",
    "battery_soc",
)


def build_dispatch_problem(horizon: int, simulation_config: SimulationConfig) -> OptimizationProblem:
    """Describe the MVP cost-minimizing dispatch problem.

    The description is metadata only: the executable CVXPY model is built by
    :class:`l6_optimization.optimizer.CVXPYOptimizer`.
    """

    if horizon <= 0:
        raise ValueError("horizon must be positive")
    return OptimizationProblem(
        problem_id="l6-24h-dispatch",
        name="cost-minimizing dispatch",
        variables=[
            DecisionVariable(variable_id=name, name=name, variable_type=DecisionVariableType.CONTINUOUS)
            for name in DISPATCH_VARIABLE_NAMES
        ],
        objectives=[
            OptimizationObjective(
                objective_id="minimize_total_cost",
                name="minimize_total_cost",
                sense=ObjectiveSense.MINIMIZE,
                expression="sum(electricity_price * grid_import * delta_hours)",
                variable_ids=["grid_import"],
            )
        ],
        constraints=[],
        parameters={"horizon": horizon, "step_size": simulation_config.step_size, "time_unit": simulation_config.time_unit},
        metadata={"status": "mvp"},
    )
