"""Minimal legacy executable model retained for pipeline compatibility."""

from __future__ import annotations

from l4_compiler.world_model_ir import WorldModel
from l5_world_model.models import Action, MetricValue, SimulationConfig, SimulationResult, SimulationTrace, WorldState
from l5_world_model.simulation.base import ExecutableWorldModel


class PlaceholderWorldModel(ExecutableWorldModel):
    def __init__(self, ir: WorldModel, *, config: SimulationConfig | None = None) -> None:
        super().__init__(ir, config=config)
        self._pending_actions: list[Action] = []
        self._trace: list[SimulationTrace] = []

    def initialize(self) -> WorldState:
        values = {state.id: state.value for state in self.ir.states}
        self._state = WorldState(time=self.config.start_time, step_index=0, values=values)
        self._pending_actions.clear()
        self._trace = [SimulationTrace(step_index=0, state=self._state)]
        return self._state

    def step(self) -> WorldState:
        if self._state is None:
            self.initialize()
        actions = list(self._pending_actions)
        self._pending_actions.clear()
        current = self._state
        values = dict(current.values)
        for action in actions:
            for key, value in action.values.items():
                if action.target_id is None or action.target_id == key or action.target_id in values:
                    values[key] = value
        next_state = current.model_copy(update={"time": current.time + self.config.step_size, "step_index": current.step_index + 1, "values": values})
        self._state = next_state
        self._trace.append(SimulationTrace(step_index=next_state.step_index, state=next_state, actions=actions))
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
            states=[item.state for item in self._trace],
            trace=list(self._trace),
            metrics=list(self.calculate_metrics()),
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

    def apply_event(self, event) -> None:
        return None

    def check_constraints(self) -> dict[str, bool]:
        return {}