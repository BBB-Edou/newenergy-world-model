"""Backward-compatible import path for the canonical L2 schema."""

from .schema import Attribute, Constraint, Entity, KnowledgeState, Objective, Process, Relation, StateVariable

State = StateVariable

__all__ = [
    "Attribute",
    "Constraint",
    "Entity",
    "KnowledgeState",
    "Objective",
    "Process",
    "Relation",
    "State",
    "StateVariable",
]