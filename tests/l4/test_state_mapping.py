from __future__ import annotations

from l3_sysml import BDD, Block, StateMachine, StateModel, StateTransition, StateVertex, SysMLModel
from l4_compiler import ModelCompiler
from l4_compiler.compiler.mappings import map_state
from l4_compiler.compiler.references import ReferenceResolver


def test_state_transition_maps_to_state_and_event() -> None:
    state_model = StateModel(
        machines=[
            StateMachine(
                id="machine-battery",
                name="Battery",
                block_id="block-battery",
                source_entity_ids=["battery"],
                states=[StateVertex(id="idle", name="Idle"), StateVertex(id="charging", name="Charging")],
                transitions=[StateTransition(id="start-charge", name="start_charge", source_state_id="idle", target_state_id="charging", trigger="charge")],
            )
        ]
    )

    states, events = map_state(state_model, {"block-battery": "entity-battery"}, ReferenceResolver())

    assert {state.name for state in states} == {"Idle", "Charging"}
    assert len(events) == 1
    assert events[0].trigger == "charge"
    assert events[0].transition_source == "state-idle"
    assert events[0].transition_target == "state-charging"

def _transition_sysml(*, include_transition: bool) -> SysMLModel:
    return SysMLModel(
        bdd=BDD(
            blocks=[
                Block(
                    id="block-battery",
                    name="Battery",
                    block_type="storage",
                    source_entity_id="battery",
                )
            ]
        ),
        state=StateModel(
            machines=[
                StateMachine(
                    id="machine-battery",
                    name="Battery",
                    block_id="block-battery",
                    source_entity_ids=["battery"],
                    states=[
                        StateVertex(id="idle", name="Idle", source_state_id="idle"),
                        StateVertex(id="charging", name="Charging", source_state_id="charging"),
                    ],
                    transitions=(
                        [
                            StateTransition(
                                id="start-charge",
                                name="start_charge",
                                source_state_id="idle",
                                target_state_id="charging",
                                trigger="charge",
                            )
                        ]
                        if include_transition
                        else []
                    ),
                )
            ]
        ),
    )


def test_compiler_maps_real_state_transition_to_event() -> None:
    world_model = ModelCompiler().compile(_transition_sysml(include_transition=True))

    assert len(world_model.states) == 2
    assert len(world_model.events) == 1
    event = world_model.events[0]
    assert event.id == "event-start-charge"
    assert event.owner == "entity-battery"
    assert event.trigger == "charge"
    assert event.transition_source == "state-idle"
    assert event.transition_target == "state-charging"
    assert event.trace[0].source_view == "State"
    assert event.trace[0].source_id == "start-charge"


def test_compiler_keeps_events_empty_without_transition() -> None:
    world_model = ModelCompiler().compile(_transition_sysml(include_transition=False))

    assert len(world_model.states) == 2
    assert world_model.events == []