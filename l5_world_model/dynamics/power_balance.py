"""Power balance and one-step battery transition."""

from __future__ import annotations

from dataclasses import dataclass

from l5_world_model.dynamics.battery import BatteryModel
from l5_world_model.models import Action


@dataclass(frozen=True, slots=True)
class StepTransition:
    next_soc: float
    wind_power: float
    pv_power: float
    load_power: float
    battery_charge: float
    battery_discharge: float
    grid_import: float
    curtailment: float
    price: float | None
    cost: float | None
    power_balance_lhs: float
    power_balance_rhs: float


def _number(value: object, *, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))


def compute_transition(
    *,
    battery: BatteryModel,
    soc: float,
    inputs: dict[str, float],
    action: Action,
    delta_hours: float,
    grid_import_limit: float | None,
) -> StepTransition:
    wind = _number(inputs.get("wind_power"))
    pv = _number(inputs.get("pv_power"))
    load = _number(inputs.get("load_power"))
    price = inputs.get("electricity_price")
    charge = max(0.0, _number(action.values.get("battery_charge")))
    discharge = max(0.0, _number(action.values.get("battery_discharge")))
    requested_grid = action.values.get("grid_import")

    net_without_grid = load + charge - wind - pv - discharge
    if requested_grid is None or requested_grid == "":
        grid_import = max(0.0, net_without_grid)
    else:
        grid_import = max(0.0, _number(requested_grid))

    generation = wind + pv
    lhs = generation + grid_import + discharge
    rhs = load + charge + max(0.0, generation + grid_import + discharge - load - charge)
    curtailment = max(0.0, generation + grid_import + discharge - load - charge)
    next_soc = battery.next_soc(soc, charge_kw=charge, discharge_kw=discharge, delta_hours=delta_hours)
    cost = grid_import * price if price is not None else None
    return StepTransition(
        next_soc=next_soc,
        wind_power=wind,
        pv_power=pv,
        load_power=load,
        battery_charge=charge,
        battery_discharge=discharge,
        grid_import=grid_import,
        curtailment=curtailment,
        price=price,
        cost=cost,
        power_balance_lhs=lhs,
        power_balance_rhs=rhs,
    )