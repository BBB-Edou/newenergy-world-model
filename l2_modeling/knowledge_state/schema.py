"""Pydantic schema for the formal L2 KnowledgeState contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class L2SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Entity(L2SchemaModel):
    id: str
    name: str
    entity_type: str
    description: str | None = None


class Attribute(L2SchemaModel):
    id: str
    entity_id: str
    name: str
    value: Any | None = None
    unit: str | None = None
    description: str | None = None


class StateVariable(L2SchemaModel):
    id: str
    entity_id: str
    name: str
    value: Any | None = None
    unit: str | None = None
    description: str | None = None


class Relation(L2SchemaModel):
    id: str
    relation_type: str
    source_entity_id: str
    target_entity_id: str
    description: str | None = None


class Process(L2SchemaModel):
    id: str
    name: str
    description: str | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)


class Constraint(L2SchemaModel):
    id: str
    name: str
    expression: str | None = None
    description: str | None = None
    variables: list[str] = Field(default_factory=list)


class Objective(L2SchemaModel):
    id: str
    name: str
    expression: str | None = None
    description: str | None = None
    direction: Literal["minimize", "maximize"]


class KnowledgeState(L2SchemaModel):
    schema_version: str = "1.0"
    entities: list[Entity] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    states: list[StateVariable] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    processes: list[Process] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    objectives: list[Objective] = Field(default_factory=list)