from __future__ import annotations

import unittest

from common import SourceRef
from l1_data import Configuration, RawArtifactKind, RawDataBundle
from l1_data.loaders.memory import InMemoryRawDataLoader


class RawModelTests(unittest.TestCase):
    def test_configuration_is_an_l1_artifact(self) -> None:
        source = SourceRef(source_id="demo-source", kind="unit-test")
        configuration = Configuration(
            artifact_id="demo-configuration",
            name="Demo",
            source=source,
            values={"components": []},
        )
        bundle = InMemoryRawDataLoader(
            bundle_id="demo-bundle",
            artifacts=(configuration,),
        ).load()

        self.assertIsInstance(bundle, RawDataBundle)
        self.assertIs(configuration.kind, RawArtifactKind.CONFIGURATION)
        self.assertEqual(list(bundle.by_kind(RawArtifactKind.CONFIGURATION)), [configuration])


if __name__ == "__main__":
    unittest.main()