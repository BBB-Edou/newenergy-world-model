"""Deterministic ScenarioInputContract generation from World Model IR."""

from __future__ import annotations

import re

from l4_compiler.world_model_ir import (
    Attribute,
    ScenarioInputContract,
    ScenarioInputSpec,
    ScenarioTimeRequirements,
    VariableType,
    WorldModel,
)

_POWER_ATTRIBUTE_NAMES = {"rated_power", "power"}
_LOAD_ATTRIBUTE_NAMES = {"demand", "load_power"}
_PRICE_ATTRIBUTE_NAMES = {"electricity_price", "price"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _entity_lookup(world_model: WorldModel) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for entity in world_model.entities:
        lookup[entity.id] = entity.id
        for trace in entity.trace:
            if trace.source_type == "knowledge_state":
                lookup[trace.source_id] = entity.id
    return lookup


def _attribute_lookup(world_model: WorldModel) -> dict[str, Attribute]:
    lookup: dict[str, Attribute] = {}
    for attribute in world_model.attributes:
        lookup[attribute.id] = attribute
        for source_id in attribute.trace:
            lookup[source_id.source_id] = attribute
        lookup[attribute.id.removeprefix("attribute-")] = attribute
    return lookup


def _contract_from_explicit_metadata(world_model: WorldModel) -> ScenarioInputContract | None:
    required = world_model.metadata.required_inputs
    if not required:
        return None
    specs = [
        ScenarioInputSpec(
            name=name,
            unit=world_model.metadata.input_units.get(name),
            data_type=VariableType.FLOAT,
            semantic_role="unknown",
            temporal=True,
            required=True,
            aliases=[name],
        )
        for name in sorted(set(required))
    ]
    return ScenarioInputContract(inputs=specs, time_requirements=_time_requirements(world_model))


def _time_requirements(world_model: WorldModel) -> ScenarioTimeRequirements:
    simulation = world_model.metadata.simulation
    return ScenarioTimeRequirements(
        step_size=simulation.step_size,
        horizon=simulation.horizon,
        time_unit=simulation.time_unit,
        start_time=0.0,
        end_time=simulation.horizon * simulation.step_size,
        timestamp_field="timestamp",
    )


def _input_name(entity_name: str, attribute_name: str) -> tuple[str, str] | None:
    attribute_slug = _slug(attribute_name)
    if attribute_slug in _POWER_ATTRIBUTE_NAMES or attribute_slug in _LOAD_ATTRIBUTE_NAMES:
        entity_slug = _slug(entity_name)
        if entity_slug.endswith("_power"):
            return entity_slug, "power"
        return f"{entity_slug}_power", "power"
    if attribute_slug in _PRICE_ATTRIBUTE_NAMES:
        return "electricity_price", "price"
    return None


def build_scenario_input_contract(world_model: WorldModel) -> ScenarioInputContract:
    explicit = _contract_from_explicit_metadata(world_model)
    if explicit is not None:
        return explicit

    entity_by_id = _entity_lookup(world_model)
    attribute_by_id = _attribute_lookup(world_model)
    candidate_entities = {
        entity_by_id[reference]
        for behavior in world_model.behaviors
        for reference in behavior.inputs + behavior.outputs
        if reference in entity_by_id
    }
    for equation in world_model.equations:
        for variable_id in equation.variables:
            attribute = attribute_by_id.get(variable_id)
            if attribute is not None:
                candidate_entities.add(attribute.owner)

    entities_by_id = {entity.id: entity for entity in world_model.entities}
    specs_by_name: dict[str, ScenarioInputSpec] = {}
    for entity_id in sorted(candidate_entities):
        entity = entities_by_id.get(entity_id)
        if entity is None:
            continue
        for attribute in sorted(world_model.attributes, key=lambda item: item.id):
            if attribute.owner != entity_id:
                continue
            named = _input_name(entity.name, attribute.name)
            if named is None:
                continue
            name, role = named
            specs_by_name[name] = ScenarioInputSpec(
                name=name,
                entity=entity.id,
                semantic_role=role,
                unit=attribute.unit,
                data_type=attribute.value_type,
                required=True,
                temporal=True,
                aliases=sorted({attribute.id, attribute.name.removeprefix("attribute-")}),
                source_ids=[entity.id, attribute.id],
            )

    for interface in world_model.interfaces:
        for variable_id in interface.variable_ids:
            if variable_id in specs_by_name:
                continue
            attribute = attribute_by_id.get(variable_id)
            specs_by_name[variable_id] = ScenarioInputSpec(
                name=variable_id,
                entity=attribute.owner if attribute else None,
                semantic_role="interface",
                unit=attribute.unit if attribute else None,
                data_type=attribute.value_type if attribute else VariableType.ANY,
                required=True,
                temporal=True,
                aliases=[variable_id],
                source_ids=[interface.id, variable_id],
            )

    return ScenarioInputContract(inputs=[specs_by_name[name] for name in sorted(specs_by_name)], time_requirements=_time_requirements(world_model))