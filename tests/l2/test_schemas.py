from __future__ import annotations

import pytest
from pydantic import ValidationError

from l2_modeling import Entity, KnowledgeState, Objective
from l2_modeling.extraction import ExtractionItem, RequirementExtraction


def test_knowledge_state_contains_exactly_seven_categories() -> None:
    state = KnowledgeState(entities=[Entity(id="wind", name="Wind", entity_type="source")])
    assert set(state.model_dump()) == {
        "schema_version",
        "entities",
        "attributes",
        "states",
        "relations",
        "processes",
        "constraints",
        "objectives",
    }


def test_knowledge_state_rejects_source_and_confidence() -> None:
    with pytest.raises(ValidationError):
        KnowledgeState.model_validate({"schema_version": "1.0", "source": "pdf"})


def test_objective_direction_is_restricted() -> None:
    with pytest.raises(ValidationError):
        Objective(id="obj", name="obj", direction="minimize_cost")


def test_extraction_category_is_restricted() -> None:
    with pytest.raises(ValidationError):
        ExtractionItem(id="x", category="sensor", name="X")


def test_requirement_extraction_shape() -> None:
    extraction = RequirementExtraction(
        document_id="doc",
        items=[ExtractionItem(id="wind", category="entity", name="Wind")],
    )
    assert extraction.items[0].category == "entity"