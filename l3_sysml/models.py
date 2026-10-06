"""Backward-compatible import path for the canonical L3 SysML schema."""

from .schema import (
    BDD,
    IBD,
    ActivityAction,
    ActivityModel,
    Block,
    BlockAttribute,
    Equation,
    IBDConnector,
    ParameterBinding,
    ParametricModel,
    Requirement,
    StateMachine,
    StateModel,
    StateTransition,
    StateVertex,
    SysMLModel,
)

Activity = ActivityAction
Parametric = ParametricModel

__all__ = [
    "BDD",
    "IBD",
    "Activity",
    "ActivityAction",
    "ActivityModel",
    "Block",
    "BlockAttribute",
    "Equation",
    "IBDConnector",
    "ParameterBinding",
    "Parametric",
    "ParametricModel",
    "Requirement",
    "StateMachine",
    "StateModel",
    "StateTransition",
    "StateVertex",
    "SysMLModel",
]