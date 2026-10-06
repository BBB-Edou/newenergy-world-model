from __future__ import annotations

from l2_modeling import Attribute, Entity, KnowledgeState, VerificationAgent
from l2_modeling.knowledge_state import Process


def _agent() -> VerificationAgent:
    return VerificationAgent()


def test_valid_state_passes() -> None:
    state = KnowledgeState(
        entities=[Entity(id="battery", name="Battery", entity_type="storage")],
        attributes=[Attribute(id="capacity", entity_id="battery", name="capacity", value=100, unit="kWh")],
    )
    assert _agent().verify(state).status == "VALID"


def test_missing_value_requests_input() -> None:
    state = KnowledgeState(
        entities=[Entity(id="battery", name="Battery", entity_type="storage")],
        attributes=[Attribute(id="capacity", entity_id="battery", name="capacity", value=None)],
    )
    result = _agent().verify(state)
    assert result.status == "NEED_INPUT"
    assert any(issue.issue_type == "missing" and issue.target_field == "value" for issue in result.issues)


def test_invalid_reference_is_invalid() -> None:
    state = KnowledgeState(
        attributes=[Attribute(id="capacity", entity_id="missing", name="capacity", value=100)]
    )
    result = _agent().verify(state)
    assert result.status == "INVALID"
    assert any(issue.issue_type == "invalid_reference" for issue in result.issues)


def test_soc_bounds_conflict_is_invalid() -> None:
    state = KnowledgeState(
        entities=[Entity(id="battery", name="Battery", entity_type="storage")],
        attributes=[
            Attribute(id="soc_min", entity_id="battery", name="SOC_min", value=90, unit="%"),
            Attribute(id="soc_max", entity_id="battery", name="SOC_max", value=20, unit="%"),
        ],
    )
    result = _agent().verify(state)
    assert result.status == "INVALID"
    assert any(issue.issue_type == "conflict" and issue.target_id == "soc_min" for issue in result.issues)


def test_duplicate_global_id_is_invalid() -> None:
    state = KnowledgeState(
        entities=[Entity(id="duplicate", name="Entity", entity_type="component")],
        processes=[Process(id="duplicate", name="Process")],
    )
    result = _agent().verify(state)
    assert result.status == "INVALID"
    assert any(issue.issue_type == "conflict" and issue.target_id == "duplicate" for issue in result.issues)