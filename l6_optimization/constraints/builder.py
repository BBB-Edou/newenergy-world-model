"""Optimization constraints matching L5 battery and power-balance semantics."""

from __future__ import annotations

import cvxpy as cp

from l5_world_model.dynamics.battery import BatteryParameters
from l6_optimization.variables import OptimizationVariables


def build_constraints(
    *,
    variables: OptimizationVariables,
    wind_power: list[float],
    pv_power: list[float],
    load_power: list[float],
    battery: BatteryParameters,
    grid_import_limit: float | None,
    delta_hours: float,
    initial_soc: float,
) -> list[cp.Constraint]:
    horizon = variables.horizon
    for name, values in (("wind_power", wind_power), ("pv_power", pv_power), ("load_power", load_power)):
        if len(values) != horizon:
            raise ValueError(f"{name} series length must match optimization horizon")

    constraints: list[cp.Constraint] = [
        variables.soc[0] == initial_soc,
        variables.soc >= battery.soc_min_pct,
        variables.soc <= battery.soc_max_pct,
        variables.charge <= battery.max_charge_kw,
        variables.discharge <= battery.max_discharge_kw,
    ]
    if grid_import_limit is not None:
        constraints.append(variables.grid_import <= grid_import_limit)

    for t in range(horizon):
        constraints.append(
            wind_power[t] + pv_power[t] + variables.grid_import[t] + variables.discharge[t]
            == load_power[t] + variables.charge[t] + variables.curtailment[t]
        )
        constraints.append(
            variables.soc[t + 1]
            == variables.soc[t]
            + battery.charge_efficiency * variables.charge[t] * delta_hours / battery.capacity_kwh * 100.0
            - variables.discharge[t] * delta_hours / (battery.discharge_efficiency * battery.capacity_kwh) * 100.0
        )
    return constraints