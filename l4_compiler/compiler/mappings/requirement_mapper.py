"""L3 Requirement -> World Model Constraint/Objective mapping."""

from __future__ import annotations

from l3_sysml import Requirement
from l4_compiler.compiler.references import ReferenceResolver
from l4_compiler.compiler.traceability import knowledge_state_trace, sysml_trace
from l4_compiler.world_model_ir import Constraint, Objective


def _sense(text: str) -> str:
    lowered = text.lower()
    if "minimize" in lowered or "minimise" in lowered:
        return "minimize"
    if "maximize" in lowered or "maximise" in lowered:
        return "maximize"
    return "undecided"


def map_requirements(
    requirements: list[Requirement],
    resolver: ReferenceResolver,
) -> tuple[list[Constraint], list[Objective]]:
    constraints: list[Constraint] = []
    objectives: list[Objective] = []
    for requirement in sorted(requirements, key=lambda item: item.id):
        source_id = requirement.source_ids[0] if requirement.source_ids else requirement.id
        scope = sorted({owner for item in requirement.source_ids if (owner := resolver.owner_of(item))})
        trace = [sysml_trace(requirement.id, "Requirements")]
        for item in requirement.source_ids:
            if requirement.requirement_type == "constraint":
                trace.append(knowledge_state_trace(item, "Constraint"))
            elif requirement.requirement_type == "objective":
                trace.append(knowledge_state_trace(item, "Objective"))
        if requirement.requirement_type == "constraint":
            constraints.append(
                Constraint(
                    id=f"constraint-{source_id}",
                    name=requirement.name,
                    expression=requirement.text,
                    scope=scope,
                    variables=[],
                    trace=trace,
                )
            )
        elif requirement.requirement_type == "objective":
            objectives.append(
                Objective(
                    id=f"objective-{source_id}",
                    name=requirement.name,
                    expression=requirement.text,
                    sense=_sense(requirement.text),  # type: ignore[arg-type]
                    scope=scope,
                    trace=trace,
                )
            )
    return constraints, objectives