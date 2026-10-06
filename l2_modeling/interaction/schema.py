"""Pydantic schemas for user clarification and deterministic state updates."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from l2_modeling.knowledge_state import KnowledgeState


class InteractionSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Question(InteractionSchemaModel):
    question_id: str
    question_type: Literal["missing", "conflict", "clarification"]
    target_type: str
    target_id: str | None = None
    target_field: str | None = None
    question: str
    reason: str


class QuestionSet(InteractionSchemaModel):
    questions: list[Question] = Field(default_factory=list)


class UserAnswer(InteractionSchemaModel):
    question_id: str
    answer: str


class StateUpdateResult(InteractionSchemaModel):
    updated: bool
    knowledge_state: KnowledgeState
    changed_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)