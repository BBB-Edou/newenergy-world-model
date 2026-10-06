"""L1 loader protocol."""

from __future__ import annotations

from typing import Protocol

from l1_data.models import RawDataBundle


class RawDataLoader(Protocol):
    """Replaceable source adapter that produces the L1 transport object."""

    def load(self) -> RawDataBundle:
        """Load raw modeling artifacts."""
        ...