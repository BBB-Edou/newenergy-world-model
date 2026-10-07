from __future__ import annotations

import unittest

from l3_sysml import BDD, Block, BlockAttribute, ParameterBinding, ParametricModel, SysMLModel
from l4_compiler import DefaultSysMLCompiler


class SysMLCompilerTests(unittest.TestCase):
    def test_blocks_and_attributes_map_to_world_model(self) -> None:
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

        world_model = DefaultSysMLCompiler().compile(model)

        self.assertEqual(len(world_model.entities), 1)
        self.assertEqual(len(world_model.attributes), 1)
        self.assertEqual(world_model.attributes[0].owner, "entity-entity-1")
        self.assertEqual(world_model.metadata.source_model, "SysMLModel")


if __name__ == "__main__":
    unittest.main()