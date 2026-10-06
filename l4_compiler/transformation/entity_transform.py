"""Minimal transforms from the L3 six-part SysML schema to L4 IR.

Only field adaptation is implemented; no L4 behavior is added here.
"""

from __future__ import annotations

from l3_sysml import Block, ParameterBinding
from l4_compiler.world_model_ir import AttributeSpec, EntitySpec, ParameterSpec, VariableType


def map_parameter_type(value_type: str) -> VariableType:
    mapping = {
        "bool": VariableType.BOOLEAN,
        "boolean": VariableType.BOOLEAN,
        "int": VariableType.INTEGER,
        "integer": VariableType.INTEGER,
        "float": VariableType.FLOAT,
        "str": VariableType.STRING,
        "string": VariableType.STRING,
        "none": VariableType.ANY,
    }
    return mapping.get(value_type.lower(), VariableType.ANY)


def to_ir_parameter(parameter: ParameterBinding) -> ParameterSpec:
    source_id = parameter.source_attribute_id or parameter.source_state_id or parameter.id
    return ParameterSpec(
        parameter_id=f"parameter-{parameter.id}",
        name=parameter.name,
        value_type=map_parameter_type(type(parameter.value).__name__),
        unit=parameter.unit,
        default_value=parameter.value,
        source_ids=(source_id,),
        metadata={"status": "placeholder"},
    )


def to_ir_attribute(parameter: ParameterBinding, *, entity_id: str) -> AttributeSpec:
    source_id = parameter.source_attribute_id or parameter.id
    return AttributeSpec(
        attribute_id=f"attribute-{parameter.id}",
        entity_id=entity_id,
        name=parameter.name,
        value_type=map_parameter_type(type(parameter.value).__name__),
        unit=parameter.unit,
        source_ids=(source_id,),
        metadata={"status": "placeholder"},
    )


def to_ir_entity(
    block: Block,
    *,
    parameter_id_map: dict[str, str],
    attribute_id_map: dict[str, str],
) -> EntitySpec:
    source_entity_id = block.source_entity_id or block.id
    source_attribute_ids = [attribute.source_attribute_id or attribute.id for attribute in block.attributes]
    return EntitySpec(
        entity_id=f"entity-{source_entity_id}",
        name=block.name,
        entity_type=block.block_type,
        attribute_ids=tuple(
            attribute_id_map[source_id]
            for source_id in source_attribute_ids
            if source_id in attribute_id_map
        ),
        parameter_ids=tuple(
            parameter_id_map[source_id]
            for source_id in source_attribute_ids
            if source_id in parameter_id_map
        ),
        source_ids=(source_entity_id,),
        metadata={"status": "placeholder"},
    )