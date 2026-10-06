"""Minimal executable model that proves the L4 -> L5 -> L6 interface."""

from __future__ import annotations

from dataclasses import replace

from l4_compiler.world_model_ir import WorldModelIR
from l5_world_model.models import Action, MetricValue, SimulationConfig, SimulationResult, SimulationTrace, WorldState
from l5_world_model.simulation.base import ExecutableWorldModel


class PlaceholderWorldModel(ExecutableWorldModel):
    """A deterministic no-physics model."""

    def __init__(self, ir: WorldModelIR, *, config: SimulationConfig | None = None) -> None:
        super().__init__(ir, config=config)
        self._pending_actions: list[Action] = []
        self._trace: list[SimulationTrace] = []

    def initialize(self) -> WorldState:
        values = {variable.state_variable_id: variable.initial_value for variable in self.ir.state_variables}
        self._state = WorldState(time=0.0, values=values)
        self._pending_actions.clear()
        self._trace = [SimulationTrace(step_index=0, state=self._state)]
        return self._state

    def step(self) -> WorldState:
        if self._state is None:
            self.initialize()
        actions = tuple(self._pending_actions)
        self._pending_actions.clear()
        current = self._state
        values = dict(current.values)
        for action in actions:
            for key, value in action.values.items():
                if action.target_id is None or action.target_id == key or action.target_id in values:
                    values[key] = value
        next_state = replace(current, time=current.time + self.config.step_size, values=values)
        self._state = next_state
        self._trace.append(SimulationTrace(step_index=len(self._trace), state=next_state, actions=actions))
        return next_state

    def run(self) -> SimulationResult:
        initial_state = self.initialize()
        for _ in range(self.config.steps):
            self.step()
        final_state = self.get_state()
        return SimulationResult(
            simulation_id=f"{self.model_id}-simulation",
            model_id=self.model_id,
            initial_state=initial_state,
            final_state=final_state,
            trace=tuple(self._trace),
            metrics=self.calculate_metrics(),
            metadata={"status": "placeholder", "runtime": self.__class__.__name__, "configured_steps": self.config.steps},
        )

    def get_state(self) -> WorldState:
        if self._state is None:
            return self.initialize()
        return self._state

    def apply_action(self, action: Action) -> None:
        self._pending_actions.append(action)

    def calculate_metrics(self) -> tuple[MetricValue, ...]:
        state = self.get_state()
        return (
            MetricValue(name="elapsed_time", value=state.time),
            MetricValue(name="state_variable_count", value=len(state.values)),
            MetricValue(name="trace_length", value=len(self._trace)),
        )