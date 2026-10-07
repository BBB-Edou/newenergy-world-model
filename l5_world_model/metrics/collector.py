"""Per-step and summary metric calculation."""

from __future__ import annotations

from dataclasses import dataclass

from l5_world_model.dynamics.power_balance import StepTransition
from l5_world_model.models import MetricValue, StepMetrics, WorldState


@dataclass(slots=True)
class MetricsCollector:
    def step(self, *, step_index: int, timestamp: str, next_state: WorldState, transition: StepTransition, battery_state_id: str) -> StepMetrics:
        return StepMetrics(
            step_index=step_index,
            timestamp=timestamp,
            wind_power=transition.wind_power,
            pv_power=transition.pv_power,
            load_power=transition.load_power,
            battery_soc=float(next_state.values[battery_state_id]),
            battery_charge=transition.battery_charge,
            battery_discharge=transition.battery_discharge,
            grid_import=transition.grid_import,
            curtailment=transition.curtailment,
            cost=transition.cost,
        )

    def summary(self, *, step_metrics: list[StepMetrics], final_soc: float, violation_count: int) -> list[MetricValue]:
        total_generation = sum(item.wind_power + item.pv_power for item in step_metrics)
        total_curtailment = sum(item.curtailment for item in step_metrics)
        total_cost = sum(item.cost for item in step_metrics if item.cost is not None)
        has_cost = any(item.cost is not None for item in step_metrics)
        utilization = 0.0 if total_generation == 0 else (total_generation - total_curtailment) / total_generation
        return [
            MetricValue(name="total_cost", value=total_cost if has_cost else None, unit="CNY", metadata={"available": has_cost}),
            MetricValue(name="renewable_utilization", value=utilization, unit=None),
            MetricValue(name="curtailment", value=total_curtailment, unit="kWh"),
            MetricValue(name="peak_grid_import", value=max((item.grid_import for item in step_metrics), default=0.0), unit="kW"),
            MetricValue(name="final_soc", value=final_soc, unit="%"),
            MetricValue(name="constraint_violation_count", value=violation_count, unit=None),
        ]