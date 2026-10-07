"""Pydantic schemas for the L2 ScenarioData side channel."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ScenarioSchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScenarioSource(ScenarioSchemaModel):
    document: str
    table_id: str
    page: int | None = None


class DataManifest(ScenarioSchemaModel):
    scenario_id: str
    table_id: str
    time_column: str
    columns: dict[str, str]
    units: dict[str, str | None] = Field(default_factory=dict)
    time_step: str | None = None
    source: ScenarioSource


class ScenarioData(ScenarioSchemaModel):
    scenario_id: str
    time: list[str]
    variables: dict[str, list[float | int | str | None]]
    units: dict[str, str | None] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: ScenarioSource


class ScenarioExtraction(ScenarioSchemaModel):
    document_id: str
    manifests: list[DataManifest] = Field(default_factory=list)


class ScenarioUpdateResult(ScenarioSchemaModel):
    updated: bool
    scenario_data: ScenarioData
    data_manifest: DataManifest
    changed_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class UnitAlignment(ScenarioSchemaModel):
    source_unit: str | None = None
    target_unit: str | None = None
    conversion: str | None = None
    factor: float | None = None


class TimeAlignment(ScenarioSchemaModel):
    source_step: str | None = None
    target_step: str | None = None
    conversion: str | None = None


class BindingValidationSummary(ScenarioSchemaModel):
    missing_inputs: list[str] = Field(default_factory=list)
    unit_mismatches: list[str] = Field(default_factory=list)
    time_mismatch: bool = False
    semantic_uncertain: list[str] = Field(default_factory=list)
    invalid_inputs: list[str] = Field(default_factory=list)


class ScenarioInputBinding(ScenarioSchemaModel):
    world_model_ir_id: str
    scenario_id: str
    scenario_data: ScenarioData | None = None
    status: Literal["READY", "NEED_INPUT", "INVALID"] = "READY"
    variable_mapping: dict[str, str] = Field(default_factory=dict)
    unit_mapping: dict[str, UnitAlignment] = Field(default_factory=dict)
    time_mapping: TimeAlignment = Field(default_factory=TimeAlignment)
    validation_summary: BindingValidationSummary = Field(default_factory=BindingValidationSummary)