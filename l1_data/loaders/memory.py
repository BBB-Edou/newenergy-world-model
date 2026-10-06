"""In-memory loader useful for tests and future adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

from l1_data.models import RawArtifact, RawDataBundle


@dataclass(slots=True)
class InMemoryRawDataLoader:
    bundle_id: str
    artifacts: tuple[RawArtifact, ...] = field(default_factory=tuple)

    def load(self) -> RawDataBundle:
        return RawDataBundle(bundle_id=self.bundle_id, artifacts=self.artifacts)