"""Pydantic schema for the deterministic World Model IR."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IRSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VariableType(str, Enum):
    ANY = "any"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"


class TraceSource(IRSchemaModel):
    source_type: Literal["sysml", "knowledge_state", "compiler"]
    source_id: str
    source_view: str | None = None
    source_parent_id: str | None = None


class SimulationSettings(IRSchemaModel):
    step_size: float = 1.0
    horizon: int = 1
    time_unit: str = "abstract"

    @model_validator(mode="after")
    def validate_settings(self) -> "SimulationSettings":
        if self.step_size <= 0:
            raise ValueError("step_size must be positive")
        if self.horizon < 0:
            raise ValueError("horizon must be non-negative")
        return self


class WorldModelMetadata(IRSchemaModel):
    ir_id: str
    name: str
    version: str = "1.0"
    source_model: str = "SysMLModel"
    source_views: list[str] = Field(default_factory=lambda: ["Requirements", "BDD", "IBD", "Activity", "State", "Parametric"])
    simulation: SimulationSettings = Field(default_factory=SimulationSettings)
    required_inputs: list[str] = Field(default_factory=list)
    input_units: dict[str, str | None] = Field(default_factory=dict)


class Entity(IRSchemaModel):
    id: str
    name: str
    entity_type: str
    description: str | None = None
    attribute_ids: list[str] = Field(default_factory=list)
    state_ids: list[str] = Field(default_factory=list)
    behavior_ids: list[str] = Field(default_factory=list)
    interface_ids: list[str] = Field(default_factory=list)
    trace: list[TraceSource] = Field(default_factory=list)


class Attribute(IRSchemaModel):
    id: str
    owner: str
    name: str
    value: Any | None = None
    unit: str | None = None
    value_type: VariableType = VariableType.ANY
    trace: list[TraceSource] = Field(default_factory=list)


class State(IRSchemaModel):
    id: str
    owner: str
    name: str
    value: Any | None = None
    unit: str | None = None
    description: str | None = None
    trace: list[TraceSource] = Field(default_factory=list)


class Behavior(IRSchemaModel):
    id: str
    owner: str | None = None
    name: str
    description: str | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    trace: list[TraceSource] = Field(default_factory=list)


class Event(IRSchemaModel):
    id: str
    name: str
    owner: str | None = None
    trigger: str | None = None
    effect: str | None = None
    transition_source: str | None = None
    transition_target: str | None = None
    condition: str | None = None
    trace: list[TraceSource] = Field(default_factory=list)


class Equation(IRSchemaModel):
    id: str
    name: str
    expression: str
    variables: list[str] = Field(default_factory=list)
    units: dict[str, str | None] = Field(default_factory=dict)
    trace: list[TraceSource] = Field(default_factory=list)


class Constraint(IRSchemaModel):
    id: str
    name: str
    expression: str
    scope: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    trace: list[TraceSource] = Field(default_factory=list)


class Objective(IRSchemaModel):
    id: str
    name: str
    expression: str
    sense: Literal["minimize", "maximize", "undecided"] = "undecided"
    scope: list[str] = Field(default_factory=list)
    trace: list[TraceSource] = Field(default_factory=list)


class Interface(IRSchemaModel):
    id: str
    name: str
    source: str
    target: str
    interface_type: str = "association"
    variable_ids: list[str] = Field(default_factory=list)
    trace: list[TraceSource] = Field(default_factory=list)


class ScenarioInputSpec(IRSchemaModel):
    name: str
    entity: str | None = None
    semantic_role: str = "unknown"
    unit: str | None = None
    data_type: VariableType = VariableType.ANY
    required: bool = True
    temporal: bool = True
    aliases: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class ScenarioTimeRequirements(IRSchemaModel):
    step_size: float = 1.0
    horizon: int = 1
    time_unit: str = "abstract"
    start_time: float | None = None
    end_time: float | None = None
    timestamp_field: str = "timestamp"


class ScenarioInputContract(IRSchemaModel):
    inputs: list[ScenarioInputSpec] = Field(default_factory=list)
    time_requirements: ScenarioTimeRequirements = Field(default_factory=ScenarioTimeRequirements)


class WorldModel(IRSchemaModel):
    metadata: WorldModelMetadata
    scenario_input_contract: ScenarioInputContract | None = None
    entities: list[Entity] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    states: list[State] = Field(default_factory=list)
    behaviors: list[Behavior] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    equations: list[Equation] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    objectives: list[Objective] = Field(default_factory=list)
    interfaces: list[Interface] = Field(default_factory=list)


WorldModelIR = WorldModel
SimulationStepSpec = SimulationSettings