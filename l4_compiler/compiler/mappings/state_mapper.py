"""State Machine -> World Model State/Event mapping."""

from __future__ import annotations

from l3_sysml import StateModel
from l4_compiler.compiler.references import ReferenceResolver
from l4_compiler.compiler.traceability import knowledge_state_trace, sysml_trace
from l4_compiler.world_model_ir import Event, State


def map_state(
    state_model: StateModel,
    entity_id_by_block: dict[str, str],
    resolver: ReferenceResolver,
) -> tuple[list[State], list[Event]]:
    states: list[State] = []
    events: list[Event] = []

    for machine in sorted(state_model.machines, key=lambda item: item.id):
        owner = entity_id_by_block.get(machine.block_id) if machine.block_id else None
        if owner is None and machine.source_entity_ids:
            owner = resolver.resolve(machine.source_entity_ids[0])
        source_owner = machine.source_entity_ids[0] if machine.source_entity_ids else machine.block_id
        if owner is None:
            raise ValueError(f"state machine {machine.id!r} has no resolvable owner")

        state_id_map: dict[str, str] = {}
        for state_vertex in sorted(machine.states, key=lambda item: item.id):
            source_state_id = state_vertex.source_state_id or state_vertex.id
            state_id = f"state-{source_state_id}"
            state_id_map[state_vertex.id] = state_id
            state_id_map[source_state_id] = state_id
            trace = [sysml_trace(state_vertex.id, "State", parent_id=machine.id)]
            if state_vertex.source_state_id:
                trace.append(knowledge_state_trace(state_vertex.source_state_id, "StateVariable", parent_id=source_owner))
            states.append(
                State(
                    id=state_id,
                    owner=owner,
                    name=state_vertex.name,
                    value=state_vertex.value,
                    unit=state_vertex.unit,
                    description=state_vertex.description,
                    trace=trace,
                )
            )

        for transition in sorted(machine.transitions, key=lambda item: item.id):
            source_state = state_id_map.get(transition.source_state_id)
            target_state = state_id_map.get(transition.target_state_id)
            if source_state is None or target_state is None:
                raise ValueError(f"transition {transition.id!r} references an unknown state")
            events.append(
                Event(
                    id=f"event-{transition.id}",
                    name=transition.name,
                    owner=owner,
                    trigger=transition.trigger,
                    effect=transition.effect,
                    transition_source=source_state,
                    transition_target=target_state,
                    condition=transition.description,
                    trace=[sysml_trace(transition.id, "State", parent_id=machine.id)],
                )
            )

    return states, events