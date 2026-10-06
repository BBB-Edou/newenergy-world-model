"""Independent World Model IR.

The IR deliberately contains no SysML classes and no dependency on a specific
simulation engine. L5 consumes these objects directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from common import Metadata


class VariableType(str, Enum):
    ANY = "any"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"


class DynamicsKind(str, Enum):
    UNSPECIFIED = "unspecified"
    ALGEBRAIC = "algebraic"
    DIFFERENCE = "difference"
    DIFFERENTIAL = "differential"
    EVENT_DRIVEN = "event_driven"


class ObjectiveSense(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    UNDECIDED = "undecided"


@dataclass(frozen=True, slots=True, kw_only=True)
class WorldSpec:
    world_id: str
    name: str
    entity_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class AttributeSpec:
    attribute_id: str
    entity_id: str
    name: str
    value_type: VariableType = VariableType.ANY
    unit: str | None = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class ParameterSpec:
    parameter_id: str
    name: str
    value_type: VariableType = VariableType.ANY
    unit: str | None = None
    default_value: Any = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class StateVariableSpec:
    state_variable_id: str
    entity_id: str
    name: str
    value_type: VariableType = VariableType.ANY
    unit: str | None = None
    initial_value: Any = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class BehaviorSpec:
    behavior_id: str
    name: str
    kind: DynamicsKind = DynamicsKind.UNSPECIFIED
    entity_ids: tuple[str, ...] = ()
    input_variable_ids: tuple[str, ...] = ()
    output_variable_ids: tuple[str, ...] = ()
    expression: str | None = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class ResourceSpec:
    resource_id: str
    name: str
    resource_type: str = "unspecified"
    unit: str | None = None
    entity_id: str | None = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitySpec:
    entity_id: str
    name: str
    entity_type: str
    attribute_ids: tuple[str, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    state_variable_ids: tuple[str, ...] = ()
    behavior_ids: tuple[str, ...] = ()
    dynamics_ids: tuple[str, ...] = ()
    interface_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class DynamicsSpec:
    dynamics_id: str
    name: str
    kind: DynamicsKind = DynamicsKind.UNSPECIFIED
    state_variable_ids: tuple[str, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    expression: str | None = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class EventSpec:
    event_id: str
    name: str
    trigger: str | None = None
    effect: str | None = None
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class InterfaceSpec:
    interface_id: str
    name: str
    source_entity_id: str
    target_entity_id: str
    variable_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstraintSpec:
    constraint_id: str
    name: str
    expression: str | None = None
    variable_ids: tuple[str, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class EquationSpec:
    equation_id: str
    name: str
    expression: str | None = None
    variable_ids: tuple[str, ...] = ()
    parameter_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectiveSpec:
    objective_id: str
    name: str
    sense: ObjectiveSense = ObjectiveSense.UNDECIDED
    expression: str | None = None
    variable_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    metadata: Metadata = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationStepSpec:
    step_size: float = 1.0
    horizon: int = 1
    time_unit: str = "abstract"
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")
        if self.horizon < 0:
            raise ValueError("horizon must be non-negative")


@dataclass(frozen=True, slots=True, kw_only=True)
class WorldModelIR:
    ir_id: str
    version: str = "0.1.0"
    world: WorldSpec | None = None
    entities: tuple[EntitySpec, ...] = ()
    attributes: tuple[AttributeSpec, ...] = ()
    state_variables: tuple[StateVariableSpec, ...] = ()
    parameters: tuple[ParameterSpec, ...] = ()
    behaviors: tuple[BehaviorSpec, ...] = ()
    dynamics: tuple[DynamicsSpec, ...] = ()
    events: tuple[EventSpec, ...] = ()
    resources: tuple[ResourceSpec, ...] = ()
    interfaces: tuple[InterfaceSpec, ...] = ()
    constraints: tuple[ConstraintSpec, ...] = ()
    equations: tuple[EquationSpec, ...] = ()
    objectives: tuple[ObjectiveSpec, ...] = ()
    simulation: SimulationStepSpec = field(default_factory=SimulationStepSpec)
    metadata: Metadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        all_ids = [] if self.world is None else [self.world.world_id]
        all_ids += [item.entity_id for item in self.entities]
        all_ids += [item.attribute_id for item in self.attributes]
        all_ids += [item.state_variable_id for item in self.state_variables]
        all_ids += [item.parameter_id for item in self.parameters]
        all_ids += [item.behavior_id for item in self.behaviors]
        all_ids += [item.dynamics_id for item in self.dynamics]
        all_ids += [item.event_id for item in self.events]
        all_ids += [item.resource_id for item in self.resources]
        all_ids += [item.interface_id for item in self.interfaces]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("World Model IR element ids must be unique")