"""Deterministic L5 discrete-time world model runtime."""

from __future__ import annotations

import re

from l2_modeling.scenario import ScenarioData, ScenarioInputBinding
from l4_compiler.world_model_ir import WorldModel
from l5_world_model.actions import ActionPolicy, ZeroActionPolicy
from l5_world_model.constraints import ConstraintEvaluator
from l5_world_model.dynamics.battery import BatteryModel, resolve_battery_parameters
from l5_world_model.dynamics.power_balance import compute_transition
from l5_world_model.events import EventProcessor
from l5_world_model.metrics import MetricsCollector
from l5_world_model.models import SimulationConfig, SimulationResult, SimulationStepRecord, SimulationTrace, WorldState
from l5_world_model.simulation.input_provider import ScenarioInputProvider, SimulationInputError
from scenario_binding.units import UnitAlignmentError, conversion_for


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _resolve_grid_limit(world_model: WorldModel) -> float | None:
    grid_owner = next((entity.id for entity in world_model.entities if entity.name.strip().lower() == "grid"), None)
    if grid_owner is None:
        return None
    attribute = next((item for item in world_model.attributes if item.owner == grid_owner and _normalize_name(item.name) in {"max_import_power", "grid_power_limit"}), None)
    if attribute is None or attribute.value is None or attribute.unit is None:
        return None
    try:
        conversion = conversion_for(attribute.unit, "kW")
    except UnitAlignmentError as exc:
        raise SimulationInputError(f"invalid Grid power limit unit: {exc}") from exc
    return float(attribute.value) * (conversion.factor if conversion else 1.0)


class WorldModelRuntime:
    def __init__(
        self,
        *,
        world_model: WorldModel,
        binding: ScenarioInputBinding,
        scenario: ScenarioData | None = None,
        config: SimulationConfig | None = None,
        initial_state: WorldState | None = None,
        action_policy: ActionPolicy | None = None,
    ) -> None:
        self.world_model = world_model
        self.binding = binding
        self.scenario = scenario or binding.scenario_data
        if self.scenario is None:
            raise SimulationInputError("ScenarioData is required; pass scenario=... or use a binding produced by ScenarioAlignment")
        self.config = config or SimulationConfig()
        self.initial_state_override = initial_state
        self.action_policy = action_policy or ZeroActionPolicy()
        self.input_provider = ScenarioInputProvider(binding, self.scenario)
        self.battery_parameters = resolve_battery_parameters(world_model, config)
        self.battery_model = BatteryModel(self.battery_parameters)
        self.grid_import_limit = _resolve_grid_limit(world_model)
        self.constraints = ConstraintEvaluator()
        self.events = EventProcessor()
        self.metrics = MetricsCollector()
        if binding.world_model_ir_id != world_model.metadata.ir_id:
            raise SimulationInputError("ScenarioInputBinding.world_model_ir_id does not match WorldModelIR")

    def initialize(self) -> WorldState:
        if self.initial_state_override is not None:
            state = self.initial_state_override
            if self.battery_parameters.state_id not in state.values:
                raise SimulationInputError(f"initial state is missing {self.battery_parameters.state_id}")
            return state
        values = {state.id: state.value for state in self.world_model.states if state.value is not None}
        if self.battery_parameters.state_id not in values:
            raise SimulationInputError(f"WorldModelIR state {self.battery_parameters.state_id} has no initial value")
        return WorldState(time=self.config.start_time, step_index=0, values=values, metadata={"status": "initialized"})

    def run(self) -> SimulationResult:
        if self.config.steps <= 0:
            return self._empty_result()
        try:
            delta_hours = self._delta_hours()
        except ValueError as exc:
            raise SimulationInputError(str(exc)) from exc
        initial = self.initialize()
        state = initial
        states = [initial]
        actions = []
        inputs_history: list[dict[str, float]] = []
        all_events = self.events.start(time=state.time, step_index=0)
        all_violations = []
        step_metrics = []
        records: list[SimulationStepRecord] = []
        trace = [SimulationTrace(step_index=0, state=initial)]

        for step_index in range(self.config.steps):
            timestamp = self.input_provider.timestamp(step_index)
            inputs = self.input_provider.get_inputs(step_index)
            action = self.action_policy.action(state, inputs, step_index)
            transition = compute_transition(
                battery=self.battery_model,
                soc=float(state.values[self.battery_parameters.state_id]),
                inputs=inputs,
                action=action,
                delta_hours=delta_hours,
                grid_import_limit=self.grid_import_limit,
            )
            next_values = dict(state.values)
            next_values[self.battery_parameters.state_id] = transition.next_soc
            next_time = self.config.start_time + (step_index + 1) * self.config.step_size
            next_state = WorldState(time=next_time, step_index=step_index + 1, values=next_values, metadata={"status": "running"})
            evaluation = self.constraints.evaluate(
                state=state,
                next_state=next_state,
                transition=transition,
                action=action,
                battery=self.battery_parameters,
                grid_import_limit=self.grid_import_limit,
                step_index=step_index,
                time=next_time,
            )
            events = self.events.step(
                before=state,
                after=next_state,
                transition=transition,
                evaluation=evaluation,
                battery=self.battery_parameters,
                step_index=step_index,
                time=next_time,
                grid_import_limit=self.grid_import_limit,
            )
            metrics = self.metrics.step(step_index=step_index, timestamp=timestamp, next_state=next_state, transition=transition, battery_state_id=self.battery_parameters.state_id)
            record = SimulationStepRecord(
                step_index=step_index,
                time=next_time,
                timestamp=timestamp,
                state_before=state,
                state_after=next_state,
                inputs=inputs,
                action=action,
                constraint_evaluation=evaluation,
                events=events,
                metrics=metrics,
            )
            records.append(record)
            step_metrics.append(metrics)
            states.append(next_state)
            actions.append(action)
            inputs_history.append(inputs)
            all_events.extend(events)
            all_violations.extend(evaluation.violations)
            trace.append(SimulationTrace(step_index=record.step_index, state=next_state, actions=[action], inputs=inputs, events=events, constraint_violations=evaluation.violations, metrics=metrics))
            state = next_state

        all_events.extend(self.events.end(time=state.time, step_index=self.config.steps))
        summary = self.metrics.summary(step_metrics=step_metrics, final_soc=float(state.values[self.battery_parameters.state_id]), violation_count=len(all_violations))
        return SimulationResult(
            simulation_id=f"{self.world_model.metadata.ir_id}-{self.scenario.scenario_id}-simulation",
            model_id=self.world_model.metadata.ir_id,
            status="COMPLETED",
            metadata={"scenario_id": self.scenario.scenario_id, "binding_status": self.binding.status, "steps": self.config.steps, "step_size": self.config.step_size, "time_unit": self.config.time_unit},
            initial_state=initial,
            final_state=state,
            states=states,
            actions=actions,
            inputs=inputs_history,
            events=all_events,
            constraint_violations=all_violations,
            metrics=summary,
            step_metrics=step_metrics,
            steps=records,
            trace=trace,
        )

    def _empty_result(self) -> SimulationResult:
        state = self.initialize()
        return SimulationResult(
            simulation_id=f"{self.world_model.metadata.ir_id}-{self.scenario.scenario_id}-simulation",
            model_id=self.world_model.metadata.ir_id,
            status="COMPLETED",
            metadata={"scenario_id": self.scenario.scenario_id, "binding_status": self.binding.status, "steps": 0},
            initial_state=state,
            final_state=state,
            states=[state],
            metrics=self.metrics.summary(step_metrics=[], final_soc=float(state.values[self.battery_parameters.state_id]), violation_count=0),
            trace=[SimulationTrace(step_index=0, state=state)],
        )

    def _delta_hours(self) -> float:
        unit = self.config.time_unit.lower()
        if unit in {"h", "hr", "hour", "hours", "小时"}:
            return self.config.step_size
        if unit in {"m", "min", "minute", "minutes", "分钟"}:
            return self.config.step_size / 60.0
        if unit in {"s", "sec", "second", "seconds", "秒"}:
            return self.config.step_size / 3600.0
        raise ValueError(f"unsupported simulation time unit: {self.config.time_unit}")


class SimulationEngine:
    def run(self, **kwargs) -> SimulationResult:
        return WorldModelRuntime(**kwargs).run()