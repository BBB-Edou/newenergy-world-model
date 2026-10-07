from __future__ import annotations

from l4_compiler import validate_world_model
from l4_compiler.world_model_ir import Attribute, WorldModel, WorldModelMetadata


def test_invalid_ir_reports_clear_reference_error() -> None:
    model = WorldModel(metadata=WorldModelMetadata(ir_id="bad", name="Bad"), attributes=[Attribute(id="attribute-x", owner="entity-missing", name="x")])
    report = validate_world_model(model)
    assert not report.valid
    assert report.issues[0].code == "attribute.owner_missing"