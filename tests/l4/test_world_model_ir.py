from __future__ import annotations

from l4_compiler import validate_world_model
from l4_compiler.world_model_ir import Attribute, Entity, State, WorldModel, WorldModelMetadata


def _valid_model() -> WorldModel:
    entity = Entity(id="entity-battery", name="Battery", entity_type="storage", attribute_ids=["attribute-capacity"], state_ids=["state-soc"])
    return WorldModel(
        metadata=WorldModelMetadata(ir_id="ir-test", name="Test World"),
        entities=[entity],
        attributes=[Attribute(id="attribute-capacity", owner="entity-battery", name="capacity", value=100)],
        states=[State(id="state-soc", owner="entity-battery", name="SOC", value=50)],
    )


def test_world_model_serializes_and_roundtrips() -> None:
    model = _valid_model()
    payload = model.model_dump_json()
    restored = WorldModel.model_validate_json(payload)
    assert restored == model


def test_world_model_validation_rejects_missing_owner() -> None:
    model = WorldModel(
        metadata=WorldModelMetadata(ir_id="bad", name="Bad"),
        attributes=[Attribute(id="attribute-x", owner="missing", name="x")],
    )
    report = validate_world_model(model)
    assert report.valid is False
    assert any(issue.code == "attribute.owner_missing" for issue in report.issues)

def test_world_model_has_exactly_ten_top_level_sections() -> None:
    assert set(_valid_model().model_dump()) == {
        "metadata",
        "entities",
        "attributes",
        "states",
        "behaviors",
        "events",
        "equations",
        "constraints",
        "objectives",
        "interfaces",
    }