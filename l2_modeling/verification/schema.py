"""Pydantic schemas for deterministic KnowledgeState verification."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VerificationSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class VerificationIssue(VerificationSchemaModel):
    issue_id: str
    severity: Literal["error", "warning", "info"]
    issue_type: Literal[
        "missing",
        "conflict",
        "invalid_type",
        "invalid_value",
        "invalid_reference",
        "constraint_error",
        "other",
    ]
    message: str
    target_type: str | None = None
    target_id: str | None = None
    target_field: str | None = None


class VerificationResult(VerificationSchemaModel):
    status: Literal["VALID", "NEED_INPUT", "INVALID"]
    issues: list[VerificationIssue] = Field(default_factory=list)