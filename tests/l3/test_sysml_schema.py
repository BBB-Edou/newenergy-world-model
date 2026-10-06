from __future__ import annotations

from l2_modeling import KnowledgeState
from l3_sysml import SysMLModel


def test_sysml_model_has_exactly_six_top_level_sections() -> None:
    model = SysMLModel()
    assert set(model.model_dump()) == {"requirements", "bdd", "ibd", "activity", "state", "parametric"}


def test_sysml_model_serializes_and_roundtrips() -> None:
    model = SysMLModel()
    payload = model.model_dump_json()
    restored = SysMLModel.model_validate_json(payload)
    assert restored == model