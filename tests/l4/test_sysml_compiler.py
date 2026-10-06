from __future__ import annotations

import unittest

from l3_sysml import Block, Parameter, SysMLModel
from l4_compiler import DefaultSysMLCompiler


class SysMLCompilerTests(unittest.TestCase):
    def test_parameters_and_blocks_map_to_independent_ir(self) -> None:
        model = SysMLModel(
            model_id="model-1",
            name="Model 1",
            parameters=(Parameter(parameter_id="p1", name="P1", value_type="float"),),
            blocks=(Block(block_id="b1", name="Block 1", parameter_ids=("p1",)),),
        )

        ir = DefaultSysMLCompiler().compile(model)

        self.assertEqual(len(ir.entities), 1)
        self.assertEqual(len(ir.parameters), 1)
        self.assertEqual(ir.entities[0].parameter_ids, (ir.parameters[0].parameter_id,))
        self.assertEqual(ir.metadata["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()