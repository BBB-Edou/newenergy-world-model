"""Deterministic constraint evaluation for the L5 runtime."""

from __future__ import annotations

from dataclasses import dataclass

from l5_world_model.dynamics.battery import BatteryParameters
from l5_world_model.dynamics.power_balance import StepTransition
from l5_world_model.models import Action, ConstraintEvaluation, ConstraintViolation, WorldState


@dataclass(slots=True)
class ConstraintEvaluator:
    power_balance_tolerance: float = 1e-6

    def evaluate(self, *, state: WorldState, next_state: WorldState, transition: StepTransition, action: Action, battery: BatteryParameters, grid_import_limit: float | None, step_index: int, time: float) -> ConstraintEvaluation:
        violations: list[ConstraintViolation] = []
        checked = ["battery_soc", "charge_power", "discharge_power", "grid_power", "power_balance"]
        next_soc = float(next_state.values[battery.state_id])
        raw_charge = action.values.get("battery_charge", 0)
        raw_discharge = action.values.get("battery_discharge", 0)
        if raw_charge is not None and float(raw_charge) < 0:
            self._violation(violations, "negative_charge_power", "battery charge power must be non-negative", step_index, time)
        if raw_discharge is not None and float(raw_discharge) < 0:
            self._violation(violations, "negative_discharge_power", "battery discharge power must be non-negative", step_index, time)
        if next_soc < battery.soc_min_pct or next_soc > battery.soc_max_pct:
            self._violation(violations, "soc_bounds", f"SOC {next_soc} outside [{battery.soc_min_pct}, {battery.soc_max_pct}]", step_index, time)
        if transition.battery_charge > battery.max_charge_kw:
            self._violation(violations, "charge_power_limit", f"charge power {transition.battery_charge} exceeds {battery.max_charge_kw} kW", step_index, time)
        if transition.battery_discharge > battery.max_discharge_kw:
            self._violation(violations, "discharge_power_limit", f"discharge power {transition.battery_discharge} exceeds {battery.max_discharge_kw} kW", step_index, time)
        if grid_import_limit is not None and transition.grid_import > grid_import_limit:
            self._violation(violations, "grid_limit", f"grid import {transition.grid_import} exceeds {grid_import_limit} kW", step_index, time)
        if abs(transition.power_balance_lhs - transition.power_balance_rhs) > self.power_balance_tolerance:
            self._violation(violations, "power_balance", "generation + grid + discharge does not equal load + charge + curtailment", step_index, time)
        return ConstraintEvaluation(valid=not violations, violations=violations, checked_constraints=checked)

    @staticmethod
    def _violation(violations: list[ConstraintViolation], code: str, message: str, step_index: int, time: float) -> None:
        violations.append(ConstraintViolation(code=code, message=message, step_index=step_index, time=time))