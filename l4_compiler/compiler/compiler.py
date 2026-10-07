"""Deterministic SysMLModel -> World Model IR compiler."""

from __future__ import annotations

from pathlib import Path

from l3_sysml import SysMLModel
from l4_compiler.compiler.ir_validator import assert_valid_world_model
from l4_compiler.compiler.loader import load_sysml
from l4_compiler.compiler.mappings import map_activity, map_bdd, map_ibd, map_parametric, map_requirements, map_state
from l4_compiler.compiler.normalizer import SysMLNormalizer
from l4_compiler.compiler.references import ReferenceResolver
from l4_compiler.compiler.validator import SysMLValidationError, SysMLValidator
from l4_compiler.world_model_ir import SimulationSettings, WorldModel, WorldModelMetadata


class ModelCompiler:
    def __init__(self) -> None:
        self.loader = load_sysml
        self.validator = SysMLValidator()
        self.normalizer = SysMLNormalizer()

    def compile(
        self,
        sysml_model: SysMLModel | dict | str | Path,
        *,
        simulation: SimulationSettings | None = None,
    ) -> WorldModel:
        model = self.loader(sysml_model)
        report = self.validator.validate(model)
        if not report.valid:
            raise SysMLValidationError(report)
        normalized = self.normalizer.normalize(model)

        entities, attributes, entity_id_by_block, _ = map_bdd(normalized.bdd)
        resolver = ReferenceResolver()
        for block in normalized.bdd.blocks:
            entity_id = entity_id_by_block[block.id]
            resolver.register(block.id, entity_id, owner=entity_id)
            if block.source_entity_id:
                resolver.register(block.source_entity_id, entity_id, owner=entity_id)
            for block_attribute in block.attributes:
                attribute_id = f"attribute-{block_attribute.source_attribute_id or block_attribute.id}"
                source_attribute_id = block_attribute.source_attribute_id or block_attribute.id
                resolver.register(source_attribute_id, attribute_id, owner=entity_id, unit=block_attribute.unit)

        interfaces = map_ibd(normalized.ibd, entity_id_by_block)
        states, events = map_state(normalized.state, entity_id_by_block, resolver)
        for state in states:
            resolver.register(state.id, state.id, owner=state.owner, unit=state.unit)
            for trace in state.trace:
                if trace.source_type == "knowledge_state":
                    resolver.register(trace.source_id, state.id, owner=state.owner, unit=state.unit)

        behaviors = map_activity(normalized.activity, resolver)
        requirement_constraints, objectives = map_requirements(normalized.requirements, resolver)
        existing_constraint_sources = {
            trace.source_id
            for constraint in requirement_constraints
            for trace in constraint.trace
            if trace.source_type == "knowledge_state" and trace.source_view == "Constraint"
        }
        equations, parametric_constraints = map_parametric(normalized.parametric, resolver, existing_constraint_sources)
        constraints = _unique_by_id([*requirement_constraints, *parametric_constraints])

        entity_references: dict[str, dict[str, list[str]]] = {
            entity.id: {"attribute_ids": [], "state_ids": [], "behavior_ids": [], "interface_ids": []}
            for entity in entities
        }
        for attribute in attributes:
            entity_references[attribute.owner]["attribute_ids"].append(attribute.id)
        for state in states:
            entity_references[state.owner]["state_ids"].append(state.id)
        for behavior in behaviors:
            if behavior.owner:
                entity_references[behavior.owner]["behavior_ids"].append(behavior.id)
        for interface in interfaces:
            entity_references[interface.source]["interface_ids"].append(interface.id)
            entity_references[interface.target]["interface_ids"].append(interface.id)
        entities = [
            entity.model_copy(update={key: sorted(value) for key, value in entity_references[entity.id].items()})
            for entity in entities
        ]

        world_model = WorldModel(
            metadata=WorldModelMetadata(
                ir_id="world-model-ir",
                name="World Model IR",
                source_model="SysMLModel",
                simulation=simulation or SimulationSettings(),
            ),
            entities=entities,
            attributes=attributes,
            states=states,
            behaviors=behaviors,
            events=events,
            equations=equations,
            constraints=constraints,
            objectives=objectives,
            interfaces=interfaces,
        )
        return assert_valid_world_model(world_model)


def compile_sysml_to_world_model(
    sysml_model: SysMLModel | dict | str | Path,
    *,
    simulation: SimulationSettings | None = None,
) -> WorldModel:
    return ModelCompiler().compile(sysml_model, simulation=simulation)


def _unique_by_id(items):
    unique = {}
    for item in sorted(items, key=lambda value: value.id):
        unique[item.id] = item
    return list(unique.values())