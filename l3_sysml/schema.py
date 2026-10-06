"""Pydantic schema for the L3 SysML model.

SysMLModel intentionally exposes exactly six top-level sections:
Requirements, BDD, IBD, Activity, State, and Parametric.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SysMLSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Requirement(SysMLSchemaModel):
    id: str
    name: str
    text: str
    requirement_type: Literal["system", "constraint", "objective"] = "system"
    source_ids: list[str] = Field(default_factory=list)


class BlockAttribute(SysMLSchemaModel):
    id: str
    name: str
    value: Any | None = None
    unit: str | None = None
    source_attribute_id: str | None = None


class Block(SysMLSchemaModel):
    id: str
    name: str
    block_type: str
    description: str | None = None
    attributes: list[BlockAttribute] = Field(default_factory=list)
    source_entity_id: str | None = None


class BDD(SysMLSchemaModel):
    name: str = "BDD"
    root_block_id: str | None = None
    blocks: list[Block] = Field(default_factory=list)


class IBDConnector(SysMLSchemaModel):
    id: str
    source_block_id: str
    target_block_id: str
    relation_type: str
    description: str | None = None
    source_relation_id: str | None = None


class IBD(SysMLSchemaModel):
    name: str = "IBD"
    block_ids: list[str] = Field(default_factory=list)
    connectors: list[IBDConnector] = Field(default_factory=list)


class ActivityAction(SysMLSchemaModel):
    id: str
    name: str
    description: str | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    source_process_id: str | None = None


class ActivityModel(SysMLSchemaModel):
    name: str = "Activity"
    actions: list[ActivityAction] = Field(default_factory=list)


class StateVertex(SysMLSchemaModel):
    id: str
    name: str
    description: str | None = None
    value: Any | None = None
    unit: str | None = None
    source_state_id: str | None = None


class StateTransition(SysMLSchemaModel):
    id: str
    name: str
    source_state_id: str
    target_state_id: str
    trigger: str | None = None
    effect: str | None = None
    description: str | None = None


class StateMachine(SysMLSchemaModel):
    id: str
    name: str
    block_id: str | None = None
    states: list[StateVertex] = Field(default_factory=list)
    transitions: list[StateTransition] = Field(default_factory=list)
    source_entity_ids: list[str] = Field(default_factory=list)


class StateModel(SysMLSchemaModel):
    name: str = "State"
    machines: list[StateMachine] = Field(default_factory=list)


class ParameterBinding(SysMLSchemaModel):
    id: str
    name: str
    value: Any | None = None
    unit: str | None = None
    source_attribute_id: str | None = None
    source_state_id: str | None = None


class Equation(SysMLSchemaModel):
    id: str
    name: str
    expression: str
    variable_ids: list[str] = Field(default_factory=list)
    source_constraint_ids: list[str] = Field(default_factory=list)
    source_objective_ids: list[str] = Field(default_factory=list)


class ParametricModel(SysMLSchemaModel):
    name: str = "Parametric"
    parameters: list[ParameterBinding] = Field(default_factory=list)
    equations: list[Equation] = Field(default_factory=list)


class SysMLModel(SysMLSchemaModel):
    requirements: list[Requirement] = Field(default_factory=list)
    bdd: BDD = Field(default_factory=BDD)
    ibd: IBD = Field(default_factory=IBD)
    activity: ActivityModel = Field(default_factory=ActivityModel)
    state: StateModel = Field(default_factory=StateModel)
    parametric: ParametricModel = Field(default_factory=ParametricModel)