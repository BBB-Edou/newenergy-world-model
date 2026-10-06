"""Deterministic completeness and consistency rules for KnowledgeState."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Any, Iterable

from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.verification.schema import VerificationIssue, VerificationResult


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _add(issues, *, severity, issue_type, message, target_type=None, target_id=None, target_field=None) -> None:
    issues.append(
        VerificationIssue(
            issue_id=f"{target_type or 'global'}-{target_id or 'all'}-{target_field or 'none'}-{len(issues) + 1:03d}",
            severity=severity,
            issue_type=issue_type,
            message=message,
            target_type=target_type,
            target_id=target_id,
            target_field=target_field,
        )
    )


def _all_ids(state: KnowledgeState) -> set[str]:
    groups: Iterable[Iterable[object]] = (
        state.entities,
        state.attributes,
        state.states,
        state.relations,
        state.processes,
        state.constraints,
        state.objectives,
    )
    return {str(getattr(item, "id")) for group in groups for item in group if getattr(item, "id", None)}


def _check_global_duplicates(state: KnowledgeState, issues: list[VerificationIssue]) -> None:
    locations: dict[str, list[str]] = defaultdict(list)
    groups = (
        ("entity", state.entities),
        ("attribute", state.attributes),
        ("state", state.states),
        ("relation", state.relations),
        ("process", state.processes),
        ("constraint", state.constraints),
        ("objective", state.objectives),
    )
    for target_type, values in groups:
        for item in values:
            item_id = getattr(item, "id", "")
            if item_id:
                locations[item_id].append(target_type)
    for item_id, item_types in locations.items():
        if len(item_types) > 1:
            _add(issues, severity="error", issue_type="conflict", message=f"duplicate id {item_id!r}: {', '.join(item_types)}", target_id=item_id)


def _check_entities(state: KnowledgeState, issues: list[VerificationIssue]) -> None:
    for entity in state.entities:
        if _blank(entity.id):
            _add(issues, severity="warning", issue_type="missing", message="entity id is required", target_type="entity", target_field="id")
        if _blank(entity.name):
            _add(issues, severity="warning", issue_type="missing", message="entity name is required", target_type="entity", target_id=entity.id, target_field="name")

def _check_attributes(state: KnowledgeState, entity_ids: set[str], issues: list[VerificationIssue]) -> None:
    for attribute in state.attributes:
        if _blank(attribute.id):
            _add(issues, severity="warning", issue_type="missing", message="attribute id is required", target_type="attribute", target_field="id")
        if _blank(attribute.name):
            _add(issues, severity="warning", issue_type="missing", message="attribute name is required", target_type="attribute", target_id=attribute.id, target_field="name")
        if _blank(attribute.entity_id):
            _add(issues, severity="warning", issue_type="missing", message="attribute entity_id is required", target_type="attribute", target_id=attribute.id, target_field="entity_id")
        elif attribute.entity_id not in entity_ids:
            _add(issues, severity="error", issue_type="invalid_reference", message=f"attribute references unknown entity {attribute.entity_id!r}", target_type="attribute", target_id=attribute.id, target_field="entity_id")
        if attribute.value is None:
            _add(issues, severity="warning", issue_type="missing", message="attribute value is not specified", target_type="attribute", target_id=attribute.id, target_field="value")
        elif isinstance(attribute.value, (dict, list, tuple, set)):
            _add(issues, severity="error", issue_type="invalid_type", message="attribute value must be a scalar or null", target_type="attribute", target_id=attribute.id, target_field="value")
        elif isinstance(attribute.value, float) and not math.isfinite(attribute.value):
            _add(issues, severity="error", issue_type="invalid_value", message="attribute value must be finite", target_type="attribute", target_id=attribute.id, target_field="value")


def _check_states(state: KnowledgeState, entity_ids: set[str], issues: list[VerificationIssue]) -> None:
    seen: set[tuple[str, str]] = set()
    for state_variable in state.states:
        if _blank(state_variable.id):
            _add(issues, severity="warning", issue_type="missing", message="state id is required", target_type="state", target_field="id")
        if _blank(state_variable.name):
            _add(issues, severity="warning", issue_type="missing", message="state name is required", target_type="state", target_id=state_variable.id, target_field="name")
        if _blank(state_variable.entity_id):
            _add(issues, severity="warning", issue_type="missing", message="state entity_id is required", target_type="state", target_id=state_variable.id, target_field="entity_id")
        elif state_variable.entity_id not in entity_ids:
            _add(issues, severity="error", issue_type="invalid_reference", message=f"state references unknown entity {state_variable.entity_id!r}", target_type="state", target_id=state_variable.id, target_field="entity_id")
        key = (state_variable.entity_id, state_variable.name)
        if key in seen:
            _add(issues, severity="error", issue_type="conflict", message=f"duplicate state variable {state_variable.entity_id}.{state_variable.name}", target_type="state", target_id=state_variable.id, target_field="name")
        seen.add(key)
        if state_variable.value is None:
            _add(issues, severity="warning", issue_type="missing", message="state value is not specified", target_type="state", target_id=state_variable.id, target_field="value")


def _check_relations(state: KnowledgeState, entity_ids: set[str], issues: list[VerificationIssue]) -> None:
    for relation in state.relations:
        if _blank(relation.relation_type):
            _add(issues, severity="warning", issue_type="missing", message="relation_type is required", target_type="relation", target_id=relation.id, target_field="relation_type")
        for field in ("source_entity_id", "target_entity_id"):
            endpoint = getattr(relation, field)
            if _blank(endpoint):
                _add(issues, severity="warning", issue_type="missing", message=f"{field} is required", target_type="relation", target_id=relation.id, target_field=field)
            elif endpoint not in entity_ids:
                _add(issues, severity="error", issue_type="invalid_reference", message=f"relation references unknown entity {endpoint!r}", target_type="relation", target_id=relation.id, target_field=field)
def _check_reference_list(values: list[str], owner_type: str, owner_id: str, field: str, known_ids: set[str], issues) -> None:
    for value in values:
        if value not in known_ids:
            _add(issues, severity="error", issue_type="invalid_reference", message=f"{field} references unknown id {value!r}", target_type=owner_type, target_id=owner_id, target_field=field)


def _check_processes(state: KnowledgeState, known_ids: set[str], issues) -> None:
    for process in state.processes:
        if _blank(process.name):
            _add(issues, severity="warning", issue_type="missing", message="process name is required", target_type="process", target_id=process.id, target_field="name")
        _check_reference_list(process.inputs, "process", process.id, "inputs", known_ids, issues)
        _check_reference_list(process.outputs, "process", process.id, "outputs", known_ids, issues)


def _check_constraints(state: KnowledgeState, known_ids: set[str], issues) -> None:
    for constraint in state.constraints:
        if _blank(constraint.name):
            _add(issues, severity="warning", issue_type="missing", message="constraint name is required", target_type="constraint", target_id=constraint.id, target_field="name")
        if _blank(constraint.expression):
            _add(issues, severity="warning", issue_type="missing", message="constraint expression is required", target_type="constraint", target_id=constraint.id, target_field="expression")
        _check_reference_list(constraint.variables, "constraint", constraint.id, "variables", known_ids, issues)


def _check_objectives(state: KnowledgeState, issues) -> None:
    for objective in state.objectives:
        if _blank(objective.name):
            _add(issues, severity="warning", issue_type="missing", message="objective name is required", target_type="objective", target_id=objective.id, target_field="name")
        if _blank(objective.expression):
            _add(issues, severity="warning", issue_type="missing", message="objective expression is required", target_type="objective", target_id=objective.id, target_field="expression")
        if objective.direction not in {"minimize", "maximize"}:
            _add(issues, severity="error", issue_type="invalid_value", message="objective direction must be minimize or maximize", target_type="objective", target_id=objective.id, target_field="direction")


def _bounds_key(name: str) -> tuple[str, str] | None:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    match = re.match(r"^(?P<base>.+?)[_\-]?(?P<bound>min|max)$", normalized)
    if not match:
        return None
    return match.group("base"), match.group("bound")


def _check_numeric_bounds(state: KnowledgeState, issues) -> None:
    bounds: dict[tuple[str, str], dict[str, tuple[Any, str]]] = defaultdict(dict)
    for attribute in state.attributes:
        if not _numeric(attribute.value):
            continue
        parsed = _bounds_key(attribute.name)
        if parsed is None:
            continue
        base, bound = parsed
        bounds[(attribute.entity_id, base)][bound] = (attribute.value, attribute.id)
    for (entity_id, base), values in bounds.items():
        if "min" in values and "max" in values:
            minimum, min_id = values["min"]
            maximum, max_id = values["max"]
            if minimum > maximum:
                _add(issues, severity="error", issue_type="conflict", message=f"{entity_id}.{base}_min={minimum} is greater than {base}_max={maximum} ({max_id})", target_type="attribute", target_id=min_id, target_field="value")


def verify_knowledge_state(state: KnowledgeState) -> VerificationResult:
    issues: list[VerificationIssue] = []
    entity_ids = {entity.id for entity in state.entities if entity.id}
    known_ids = _all_ids(state)
    _check_global_duplicates(state, issues)
    _check_entities(state, issues)
    _check_attributes(state, entity_ids, issues)
    _check_states(state, entity_ids, issues)
    _check_relations(state, entity_ids, issues)
    _check_processes(state, known_ids, issues)
    _check_constraints(state, known_ids, issues)
    _check_objectives(state, issues)
    _check_numeric_bounds(state, issues)
    if any(issue.severity == "error" for issue in issues):
        status = "INVALID"
    elif issues:
        status = "NEED_INPUT"
    else:
        status = "VALID"
    return VerificationResult(status=status, issues=issues)