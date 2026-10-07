"""Factory helpers for legacy and Scenario-aware L5 runtimes."""

from __future__ import annotations

from l2_modeling.scenario import ScenarioData, ScenarioInputBinding
from l4_compiler.world_model_ir import WorldModel
from l5_world_model.actions import ActionPolicy, ZeroActionPolicy
from l5_world_model.models import SimulationConfig, WorldState
from l5_world_model.simulation.engine import WorldModelRuntime
from l5_world_model.simulation.placeholder import PlaceholderWorldModel


def build_world_model(ir: WorldModel, *, config: SimulationConfig | None = None) -> PlaceholderWorldModel:
    return PlaceholderWorldModel(ir, config=config)


def build_runtime(
    *,
    world_model: WorldModel,
    binding: ScenarioInputBinding,
    scenario: ScenarioData | None = None,
    config: SimulationConfig | None = None,
    initial_state: WorldState | None = None,
    action_policy: ActionPolicy | None = None,
) -> WorldModelRuntime:
    return WorldModelRuntime(
        world_model=world_model,
        binding=binding,
        scenario=scenario,
        config=config or SimulationConfig(),
        initial_state=initial_state,
        action_policy=action_policy or ZeroActionPolicy(),
    )