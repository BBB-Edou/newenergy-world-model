"""Deterministic structural and reference validation for World Model IR."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from l4_compiler.world_model_ir import WorldModel


class IRValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    target_type: str | None = None
    target_id: str | None = None


class IRValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    valid: bool
    issues: list[IRValidationIssue] = Field(default_factory=list)


class IRValidationError(ValueError):
    def __init__(self, report: IRValidationReport) -> None:
        self.report = report
        details = "; ".join(issue.message for issue in report.issues)
        super().__init__(f"Invalid World Model IR: {details}")


def validate_world_model(model: WorldModel) -> IRValidationReport:
    issues: list[IRValidationIssue] = []
    entity_ids = {item.id for item in model.entities}
    attribute_ids = {item.id for item in model.attributes}
    state_ids = {item.id for item in model.states}
    behavior_ids = {item.id for item in model.behaviors}
    event_ids = {item.id for item in model.events}
    equation_ids = {item.id for item in model.equations}
    constraint_ids = {item.id for item in model.constraints}
    objective_ids = {item.id for item in model.objectives}
    interface_ids = {item.id for item in model.interfaces}
    all_ids = entity_ids | attribute_ids | state_ids | behavior_ids | event_ids | equation_ids | constraint_ids | objective_ids | interface_ids

    _check_duplicates(model, issues)
    for attribute in model.attributes:
        if attribute.owner not in entity_ids:
            _issue(issues, "attribute.owner_missing", f"attribute owner {attribute.owner!r} does not exist", "Attribute", attribute.id)
    for state in model.states:
        if state.owner not in entity_ids:
            _issue(issues, "state.owner_missing", f"state owner {state.owner!r} does not exist", "State", state.id)
    for behavior in model.behaviors:
        if behavior.owner and behavior.owner not in entity_ids:
            _issue(issues, "behavior.owner_missing", f"behavior owner {behavior.owner!r} does not exist", "Behavior", behavior.id)
        _check_refs(behavior.inputs, all_ids, "behavior.input_missing", "Behavior", behavior.id, issues)
        _check_refs(behavior.outputs, all_ids, "behavior.output_missing", "Behavior", behavior.id, issues)
    for event in model.events:
        if event.owner and event.owner not in entity_ids:
            _issue(issues, "event.owner_missing", f"event owner {event.owner!r} does not exist", "Event", event.id)
        if event.transition_source and event.transition_source not in state_ids:
            _issue(issues, "event.source_missing", f"event source {event.transition_source!r} does not exist", "Event", event.id)
        if event.transition_target and event.transition_target not in state_ids:
            _issue(issues, "event.target_missing", f"event target {event.transition_target!r} does not exist", "Event", event.id)
    for equation in model.equations:
        if not equation.expression.strip():
            _issue(issues, "equation.expression_empty", f"equation {equation.id!r} has an empty expression", "Equation", equation.id)
        _check_refs(equation.variables, all_ids, "equation.variable_missing", "Equation", equation.id, issues)
    for constraint in model.constraints:
        if not constraint.expression.strip():
            _issue(issues, "constraint.expression_empty", f"constraint {constraint.id!r} has an empty expression", "Constraint", constraint.id)
        _check_refs(constraint.scope, entity_ids, "constraint.scope_missing", "Constraint", constraint.id, issues)
        _check_refs(constraint.variables, all_ids, "constraint.variable_missing", "Constraint", constraint.id, issues)
    for objective in model.objectives:
        if not objective.expression.strip():
            _issue(issues, "objective.expression_empty", f"objective {objective.id!r} has an empty expression", "Objective", objective.id)
        _check_refs(objective.scope, entity_ids, "objective.scope_missing", "Objective", objective.id, issues)
    for interface in model.interfaces:
        if interface.source not in entity_ids:
            _issue(issues, "interface.source_missing", f"interface source {interface.source!r} does not exist", "Interface", interface.id)
        if interface.target not in entity_ids:
            _issue(issues, "interface.target_missing", f"interface target {interface.target!r} does not exist", "Interface", interface.id)
        _check_refs(interface.variable_ids, all_ids, "interface.variable_missing", "Interface", interface.id, issues)
    for entity in model.entities:
        _check_refs(entity.attribute_ids, attribute_ids, "entity.attribute_missing", "Entity", entity.id, issues)
        _check_refs(entity.state_ids, state_ids, "entity.state_missing", "Entity", entity.id, issues)
        _check_refs(entity.behavior_ids, behavior_ids, "entity.behavior_missing", "Entity", entity.id, issues)
        _check_refs(entity.interface_ids, interface_ids, "entity.interface_missing", "Entity", entity.id, issues)

    return IRValidationReport(valid=not issues, issues=issues)


def assert_valid_world_model(model: WorldModel) -> WorldModel:
    report = validate_world_model(model)
    if not report.valid:
        raise IRValidationError(report)
    return model


def _check_refs(values: list[str], known_ids: set[str], code: str, target_type: str, target_id: str, issues: list[IRValidationIssue]) -> None:
    for value in values:
        if value not in known_ids:
            _issue(issues, code, f"{target_type} {target_id!r} references unknown id {value!r}", target_type, target_id)


def _check_duplicates(model: WorldModel, issues: list[IRValidationIssue]) -> None:
    groups = (
        ("Entity", [item.id for item in model.entities]),
        ("Attribute", [item.id for item in model.attributes]),
        ("State", [item.id for item in model.states]),
        ("Behavior", [item.id for item in model.behaviors]),
        ("Event", [item.id for item in model.events]),
        ("Equation", [item.id for item in model.equations]),
        ("Constraint", [item.id for item in model.constraints]),
        ("Objective", [item.id for item in model.objectives]),
        ("Interface", [item.id for item in model.interfaces]),
    )
    seen: dict[str, str] = {}
    for target_type, ids in groups:
        for item_id in ids:
            if item_id in seen:
                _issue(issues, "ir.duplicate_id", f"duplicate IR id {item_id!r}", target_type, item_id)
            seen[item_id] = target_type


def _issue(issues: list[IRValidationIssue], code: str, message: str, target_type: str | None, target_id: str | None) -> None:
    issues.append(IRValidationIssue(code=code, message=message, target_type=target_type, target_id=target_id))