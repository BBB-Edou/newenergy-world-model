"""Backward-compatible import path for the World Model IR schema."""

from .schema import (
    Attribute,
    Behavior,
    Constraint,
    Entity,
    Equation,
    Event,
    Interface,
    Objective,
    SimulationSettings,
    SimulationStepSpec,
    State,
    TraceSource,
    VariableType,
    WorldModel,
    WorldModelIR,
    WorldModelMetadata,
)

# Compatibility names used by earlier skeleton iterations.
EntitySpec = Entity
AttributeSpec = Attribute
StateVariableSpec = State
ParameterSpec = Attribute
BehaviorSpec = Behavior
EventSpec = Event
EquationSpec = Equation
ConstraintSpec = Constraint
ObjectiveSpec = Objective
InterfaceSpec = Interface
WorldSpec = WorldModelMetadata

__all__ = [
    "Attribute",
    "AttributeSpec",
    "Behavior",
    "BehaviorSpec",
    "Constraint",
    "ConstraintSpec",
    "Entity",
    "EntitySpec",
    "Equation",
    "EquationSpec",
    "Event",
    "EventSpec",
    "Interface",
    "InterfaceSpec",
    "Objective",
    "ObjectiveSpec",
    "ParameterSpec",
    "SimulationSettings",
    "SimulationStepSpec",
    "State",
    "StateVariableSpec",
    "TraceSource",
    "VariableType",
    "WorldModel",
    "WorldModelIR",
    "WorldModelMetadata",
    "WorldSpec",
]