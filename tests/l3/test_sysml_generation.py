from __future__ import annotations

import unittest

from l2_modeling.knowledge_state import Entity, KnowledgeState, Relation
from l3_sysml import KnowledgeStateToSysMLGenerator


class SysMLGenerationTests(unittest.TestCase):
    def test_entities_and_relations_map_to_blocks_and_connections(self) -> None:
        state = KnowledgeState(
            entities=(Entity(id="a", name="A", entity_type="generic"), Entity(id="b", name="B", entity_type="generic")),
            relations=(Relation(id="a-to-b", source_entity_id="a", target_entity_id="b", relation_type="related_to"),),
        )

        model = KnowledgeStateToSysMLGenerator().generate(state)

        self.assertEqual(len(model.blocks), 2)
        self.assertEqual(len(model.ports), 2)
        self.assertEqual(len(model.connections), 1)
        self.assertEqual(model.metadata["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()