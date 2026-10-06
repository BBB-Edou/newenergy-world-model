"""Tool-neutral SysML subset for Phase 0."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from common import Metadata


class PortDirection(str, Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"


@dataclass(frozen=True, slots=True, kw_only=True)
class Parameter:
    parameter_id: str
    name: str
    value_type: str = "unspecified"
    unit: str | None = None
    default_value: Any = None
    source_attribute_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Port:
    port_id: str
    name: str
    port_type: str = "unspecified"
    direction: PortDirection = PortDirection.INOUT
    source_entity_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Connection:
    connection_id: str
    name: str
    source_port_id: str
    target_port_id: str
    connection_type: str = "association"
    source_relation_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Block:
    block_id: str
    name: str
    block_type: str = "block"
    port_ids: tuple[str, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    source_entity_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Requirement:
    requirement_id: str
    text: str
    requirement_type: str = "unspecified"
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Activity:
    activity_id: str
    name: str
    action_names: tuple[str, ...] = ()
    source_process_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class StateMachine:
    state_machine_id: str
    name: str
    state_names: tuple[str, ...] = ()
    initial_state: str | None = None
    transition_names: tuple[str, ...] = ()
    source_entity_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Sequence:
    sequence_id: str
    name: str
    lifeline_names: tuple[str, ...] = ()
    message_names: tuple[str, ...] = ()
    source_process_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstraintSpec:
    constraint_id: str
    name: str
    expression: str | None = None
    parameter_ids: tuple[str, ...] = ()
    source_constraint_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class Parametric:
    parametric_id: str
    name: str
    constraint_ids: tuple[str, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class SysMLModel:
    model_id: str
    name: str
    requirements: tuple[Requirement, ...] = ()
    blocks: tuple[Block, ...] = ()
    ports: tuple[Port, ...] = ()
    connections: tuple[Connection, ...] = ()
    activities: tuple[Activity, ...] = ()
    state_machines: tuple[StateMachine, ...] = ()
    sequences: tuple[Sequence, ...] = ()
    constraints: tuple[ConstraintSpec, ...] = ()
    parameters: tuple[Parameter, ...] = ()
    parametrics: tuple[Parametric, ...] = ()
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        all_ids = [item.block_id for item in self.blocks]
        all_ids += [item.port_id for item in self.ports]
        all_ids += [item.connection_id for item in self.connections]
        all_ids += [item.parameter_id for item in self.parameters]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("SysML model element ids must be unique")