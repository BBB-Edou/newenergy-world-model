"""Minimal deterministic event processing for the L5 runtime."""

from __future__ import annotations

from dataclasses import dataclass

from l5_world_model.dynamics.battery import BatteryParameters
from l5_world_model.dynamics.power_balance import StepTransition
from l5_world_model.models import ConstraintEvaluation, SimulationEvent, WorldState


@dataclass(slots=True)
class EventProcessor:
    def start(self, *, time: float, step_index: int) -> list[SimulationEvent]:
        return [SimulationEvent(event_id=f"event-start-{step_index}", event_type="SimulationStart", time=time, step_index=step_index, message="simulation started")]

    def end(self, *, time: float, step_index: int) -> list[SimulationEvent]:
        return [SimulationEvent(event_id=f"event-end-{step_index}", event_type="SimulationEnd", time=time, step_index=step_index, message="simulation ended")]

    def step(self, *, before: WorldState, after: WorldState, transition: StepTransition, evaluation: ConstraintEvaluation, battery: BatteryParameters, step_index: int, time: float, grid_import_limit: float | None) -> list[SimulationEvent]:
        events: list[SimulationEvent] = []
        for violation in evaluation.violations:
            events.append(SimulationEvent(event_id=f"event-{step_index}-{violation.code}", event_type="ConstraintViolation", time=time, step_index=step_index, message=violation.message, metadata={"code": violation.code}))
        soc = float(after.values[battery.state_id])
        if soc <= battery.soc_min_pct:
            events.append(SimulationEvent(event_id=f"event-{step_index}-soc-min", event_type="BatterySOCBoundary", time=time, step_index=step_index, message="Battery SOC reached the lower boundary", metadata={"soc": soc}))
        if soc >= battery.soc_max_pct:
            events.append(SimulationEvent(event_id=f"event-{step_index}-soc-max", event_type="BatterySOCBoundary", time=time, step_index=step_index, message="Battery SOC reached the upper boundary", metadata={"soc": soc}))
        if grid_import_limit is not None and transition.grid_import > grid_import_limit:
            events.append(SimulationEvent(event_id=f"event-{step_index}-grid-limit", event_type="GridLimitExceeded", time=time, step_index=step_index, message="Grid import limit exceeded", metadata={"grid_import": transition.grid_import, "limit": grid_import_limit}))
        return events