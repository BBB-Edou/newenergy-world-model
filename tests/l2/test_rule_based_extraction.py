from __future__ import annotations

import unittest

from common import SourceRef
from l1_data import Configuration, RawDataBundle
from l2_modeling import RuleBasedKnowledgeExtractor


class RuleBasedExtractionTests(unittest.TestCase):
    def test_structured_components_become_entities(self) -> None:
        source = SourceRef(source_id="demo-source", kind="unit-test")
        configuration = Configuration(
            artifact_id="demo-configuration",
            name="Demo",
            source=source,
            values={"components": [{"id": "asset-a", "name": "Asset A", "kind": "test_component"}, {"id": "asset-b", "name": "Asset B", "kind": "test_component"}]},
        )
        raw_data = RawDataBundle(bundle_id="demo-bundle", artifacts=(configuration,))

        knowledge_state = RuleBasedKnowledgeExtractor().extract(raw_data)

        self.assertEqual([entity.id for entity in knowledge_state.entities], ["asset-a", "asset-b"])
        self.assertEqual(knowledge_state.schema_version, "1.0")


if __name__ == "__main__":
    unittest.main()