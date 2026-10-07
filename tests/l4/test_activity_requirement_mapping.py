from __future__ import annotations

from l3_sysml import ActivityAction, ActivityModel, Requirement, SysMLModel
from l4_compiler import ModelCompiler
from l4_compiler.compiler.mappings import map_activity, map_requirements
from l4_compiler.compiler.references import ReferenceResolver


def test_activity_action_maps_to_behavior() -> None:
    resolver = ReferenceResolver()
    resolver.register("wind", "entity-wind", owner="entity-wind")
    resolver.register("load", "entity-load", owner="entity-load")
    behaviors = map_activity(
        ActivityModel(actions=[ActivityAction(id="action-generation", name="generation", inputs=["wind"], outputs=["load"], source_process_id="generation")]),
        resolver,
    )

    assert len(behaviors) == 1
    assert behaviors[0].id == "behavior-generation"
    assert behaviors[0].inputs == ["entity-wind"]
    assert behaviors[0].outputs == ["entity-load"]


def test_requirement_maps_to_constraint_and_objective() -> None:
    resolver = ReferenceResolver()
    resolver.register("soc_bounds", "state-soc", owner="entity-battery")
    constraints, objectives = map_requirements(
        [
            Requirement(id="req-soc", name="SOC bounds", text="soc_min <= soc <= soc_max", requirement_type="constraint", source_ids=["soc_bounds"]),
            Requirement(id="req-cost", name="cost", text="minimize cost", requirement_type="objective", source_ids=["cost"]),
        ],
        resolver,
    )

    assert constraints[0].id == "constraint-soc_bounds"
    assert constraints[0].scope == ["entity-battery"]
    assert objectives[0].id == "objective-cost"
    assert objectives[0].sense == "minimize"

def test_compiler_maps_explicit_requirement_to_objective() -> None:
    sysml_model = SysMLModel(
        requirements=[
            Requirement(
                id="requirement-minimize-cost",
                name="minimize_cost",
                text="minimize operating_cost",
                requirement_type="objective",
                source_ids=["minimize_operating_cost"],
            )
        ]
    )

    world_model = ModelCompiler().compile(sysml_model)

    assert len(world_model.objectives) == 1
    objective = world_model.objectives[0]
    assert objective.id == "objective-minimize_operating_cost"
    assert objective.name == "minimize_cost"
    assert objective.expression == "minimize operating_cost"
    assert objective.sense == "minimize"
    assert {(trace.source_type, trace.source_view, trace.source_id) for trace in objective.trace} == {
        ("sysml", "Requirements", "requirement-minimize-cost"),
        ("knowledge_state", "Objective", "minimize_operating_cost"),
    }


def test_compiler_does_not_create_unsourced_objectives() -> None:
    world_model = ModelCompiler().compile(SysMLModel())

    assert world_model.objectives == []