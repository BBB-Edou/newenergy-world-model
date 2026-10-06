"""Minimal structural transforms used by the Phase 0 compiler."""

from __future__ import annotations

from l3_sysml import Block, Parameter
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
    }
    return mapping.get(value_type.lower(), VariableType.ANY)


def to_ir_parameter(parameter: Parameter) -> ParameterSpec:
    return ParameterSpec(
        parameter_id=f"parameter-{parameter.parameter_id}",
        name=parameter.name,
        value_type=map_parameter_type(parameter.value_type),
        unit=parameter.unit,
        default_value=parameter.default_value,
        source_ids=(parameter.parameter_id,),
        metadata={"status": "placeholder"},
    )


def to_ir_attribute(parameter: Parameter, *, entity_id: str) -> AttributeSpec:
    return AttributeSpec(
        attribute_id=f"attribute-{parameter.parameter_id}",
        entity_id=entity_id,
        name=parameter.name,
        value_type=map_parameter_type(parameter.value_type),
        unit=parameter.unit,
        source_ids=(parameter.parameter_id,),
        metadata={"status": "placeholder"},
    )


def to_ir_entity(
    block: Block,
    *,
    parameter_id_map: dict[str, str],
    attribute_id_map: dict[str, str],
) -> EntitySpec:
    entity_id = f"entity-{block.block_id}"
    return EntitySpec(
        entity_id=entity_id,
        name=block.name,
        entity_type=block.block_type,
        attribute_ids=tuple(
            attribute_id_map[parameter_id]
            for parameter_id in block.parameter_ids
            if parameter_id in attribute_id_map
        ),
        parameter_ids=tuple(
            parameter_id_map[parameter_id]
            for parameter_id in block.parameter_ids
            if parameter_id in parameter_id_map
        ),
        source_ids=(block.block_id,),
        metadata={"status": "placeholder"},
    )