"""BDD Block/Attribute -> World Model Entity/Attribute mapping."""

from __future__ import annotations

from l3_sysml import BDD
from l4_compiler.compiler.traceability import knowledge_state_trace, sysml_trace
from l4_compiler.world_model_ir import Attribute, Entity, VariableType


def infer_value_type(value: object) -> VariableType:
    if isinstance(value, bool):
        return VariableType.BOOLEAN
    if isinstance(value, int):
        return VariableType.INTEGER
    if isinstance(value, float):
        return VariableType.FLOAT
    if isinstance(value, str):
        return VariableType.STRING
    return VariableType.ANY


def map_bdd(bdd: BDD) -> tuple[list[Entity], list[Attribute], dict[str, str], dict[str, str]]:
    entities: list[Entity] = []
    attributes: list[Attribute] = []
    entity_id_by_block: dict[str, str] = {}
    attribute_id_by_source: dict[str, str] = {}

    for block in sorted(bdd.blocks, key=lambda item: item.id):
        source_entity_id = block.source_entity_id or block.id
        entity_id = f"entity-{source_entity_id}"
        trace = [sysml_trace(block.id, "BDD")]
        if block.source_entity_id:
            trace.append(knowledge_state_trace(block.source_entity_id, "Entity"))
        entities.append(
            Entity(
                id=entity_id,
                name=block.name,
                entity_type=block.block_type,
                description=block.description,
                trace=trace,
            )
        )
        entity_id_by_block[block.id] = entity_id

        for block_attribute in sorted(block.attributes, key=lambda item: item.id):
            source_attribute_id = block_attribute.source_attribute_id or block_attribute.id
            attribute_id = f"attribute-{source_attribute_id}"
            attribute_trace = [sysml_trace(block_attribute.id, "BDD", parent_id=block.id)]
            if block_attribute.source_attribute_id:
                attribute_trace.append(knowledge_state_trace(block_attribute.source_attribute_id, "Attribute", parent_id=source_entity_id))
            attributes.append(
                Attribute(
                    id=attribute_id,
                    owner=entity_id,
                    name=block_attribute.name,
                    value=block_attribute.value,
                    unit=block_attribute.unit,
                    value_type=infer_value_type(block_attribute.value),
                    trace=attribute_trace,
                )
            )
            attribute_id_by_source[source_attribute_id] = attribute_id

    return entities, attributes, entity_id_by_block, attribute_id_by_source