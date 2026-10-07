"""Deterministic action policies used by the L5 runtime."""

from __future__ import annotations

from typing import Any, Protocol

from l5_world_model.models import Action, WorldState


class ActionPolicy(Protocol):
    def action(self, state: WorldState, inputs: dict[str, float], step_index: int) -> Action:
        ...


def _action(action_id: str, name: str, values: dict[str, Any]) -> Action:
    return Action(action_id=action_id, name=name, values=values)


class ZeroActionPolicy:
    def action(self, state: WorldState, inputs: dict[str, float], step_index: int) -> Action:
        return _action(f"zero-{step_index}", "zero", {"battery_charge": 0.0, "battery_discharge": 0.0, "grid_import": None})


class FixedActionPolicy:
    def __init__(self, values: dict[str, Any], *, name: str = "fixed") -> None:
        self.values = dict(values)
        self.name = name

    def action(self, state: WorldState, inputs: dict[str, float], step_index: int) -> Action:
        return _action(f"fixed-{step_index}", self.name, dict(self.values))


class OpenLoopActionSequence:
    def __init__(self, actions: list[Action]) -> None:
        self.actions = list(actions)

    def action(self, state: WorldState, inputs: dict[str, float], step_index: int) -> Action:
        if step_index < len(self.actions):
            return self.actions[step_index]
        return ZeroActionPolicy().action(state, inputs, step_index)