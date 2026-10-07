"""L4 -> L5 pipeline stage."""

from __future__ import annotations

from l2_modeling.scenario import ScenarioData, ScenarioInputBinding
from l4_compiler import WorldModel
from l5_world_model import (
    ActionPolicy,
    ExecutableWorldModel,
    SimulationConfig,
    WorldModelRuntime,
    WorldState,
    build_runtime,
    build_world_model,
)


def run_l4_to_l5(
    world_model_ir: WorldModel,
    *,
    binding: ScenarioInputBinding | None = None,
    scenario: ScenarioData | None = None,
    config: SimulationConfig | None = None,
    initial_state: WorldState | None = None,
    action_policy: ActionPolicy | None = None,
) -> ExecutableWorldModel | WorldModelRuntime:
    if binding is None:
        return build_world_model(world_model_ir, config=config)
    return build_runtime(
        world_model=world_model_ir,
        binding=binding,
        scenario=scenario,
        config=config,
        initial_state=initial_state,
        action_policy=action_policy,
    )