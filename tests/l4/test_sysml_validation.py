from __future__ import annotations

import pytest

from l3_sysml import BDD, IBD, IBDConnector, SysMLModel
from l4_compiler import ModelCompiler, SysMLValidationError


def test_invalid_sysml_reference_fails_with_clear_error() -> None:
    model = SysMLModel(
        bdd=BDD(blocks=[]),
        ibd=IBD(block_ids=["block-missing"], connectors=[IBDConnector(id="bad", source_block_id="block-missing", target_block_id="block-other", relation_type="supplies")]),
    )

    with pytest.raises(SysMLValidationError, match="references unknown block"):
        ModelCompiler().compile(model)