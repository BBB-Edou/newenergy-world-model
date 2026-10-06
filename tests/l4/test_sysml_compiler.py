from __future__ import annotations

import unittest

from l3_sysml import BDD, Block, BlockAttribute, ParameterBinding, ParametricModel, SysMLModel
from l4_compiler import DefaultSysMLCompiler


class SysMLCompilerTests(unittest.TestCase):
    def test_parameters_and_blocks_map_to_independent_ir(self) -> None:
        model = SysMLModel(
            bdd=BDD(
                blocks=[
                    Block(
                        id="block-1",
                        name="Block 1",
                        block_type="component",
                        attributes=[BlockAttribute(id="p1", name="P1", value=1.0, unit="kW", source_attribute_id="p1")],
                        source_entity_id="entity-1",
                    )
                ]
            ),
            parametric=ParametricModel(
                parameters=[ParameterBinding(id="p1", name="P1", value=1.0, unit="kW", source_attribute_id="p1")]
            ),
        )

        ir = DefaultSysMLCompiler().compile(model)

        self.assertEqual(len(ir.entities), 1)
        self.assertEqual(len(ir.parameters), 1)
        self.assertEqual(ir.entities[0].parameter_ids, (ir.parameters[0].parameter_id,))
        self.assertEqual(ir.metadata["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()