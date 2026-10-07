"""Compare CVXPY predicted trajectories with L5 execution."""

from __future__ import annotations

from l6_optimization.models import ConsistencyReport
from l6_optimization.variables import OptimizationVariables


class OptimizationConsistencyError(ValueError):
    pass


def compare_optimization_and_simulation(
    *,
    variables: OptimizationVariables,
    simulation_result,
    predicted_cost: float,
    tolerance: float,
) -> ConsistencyReport:
    metrics = simulation_result.step_metrics
    predicted = {
        "battery_soc": [float(value) for value in variables.soc.value[1:]],
        "battery_charge": [float(value) for value in variables.charge.value],
        "battery_discharge": [float(value) for value in variables.discharge.value],
        "grid_import": [float(value) for value in variables.grid_import.value],
        "curtailment": [float(value) for value in variables.curtailment.value],
        "total_cost": [predicted_cost],
    }
    actual = {
        "battery_soc": [item.battery_soc for item in metrics],
        "battery_charge": [item.battery_charge for item in metrics],
        "battery_discharge": [item.battery_discharge for item in metrics],
        "grid_import": [item.grid_import for item in metrics],
        "curtailment": [item.curtailment for item in metrics],
        "total_cost": [sum(item.cost or 0.0 for item in metrics)],
    }
    errors = {
        name: max(abs(left - right) for left, right in zip(predicted[name], actual[name], strict=True))
        for name in predicted
    }
    report = ConsistencyReport(valid=all(error <= tolerance for error in errors.values()), tolerance=tolerance, max_abs_error=errors)
    if not report.valid:
        raise OptimizationConsistencyError(f"Optimization and simulation trajectories differ: {errors}")
    return report