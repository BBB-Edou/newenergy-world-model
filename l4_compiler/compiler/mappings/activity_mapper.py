"""Activity Action -> World Model Behavior mapping."""

from __future__ import annotations

from l3_sysml import ActivityModel
from l4_compiler.compiler.references import ReferenceResolver
from l4_compiler.compiler.traceability import knowledge_state_trace, sysml_trace
from l4_compiler.world_model_ir import Behavior


def map_activity(activity: ActivityModel, resolver: ReferenceResolver) -> list[Behavior]:
    behaviors: list[Behavior] = []
    for action in sorted(activity.actions, key=lambda item: item.id):
        source_process_id = action.source_process_id or action.id
        inputs = resolver.resolved_list(action.inputs)
        outputs = resolver.resolved_list(action.outputs)
        owner = next((resolver.owner_of(item) for item in action.inputs if resolver.owner_of(item)), None)
        trace = [sysml_trace(action.id, "Activity")]
        if action.source_process_id:
            trace.append(knowledge_state_trace(action.source_process_id, "Process"))
        behaviors.append(
            Behavior(
                id=f"behavior-{source_process_id}",
                owner=owner,
                name=action.name,
                description=action.description,
                inputs=inputs,
                outputs=outputs,
                trace=trace,
            )
        )
    return behaviors