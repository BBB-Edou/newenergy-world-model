"""Parser interface for future SysML text/XMI adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from l3_sysml import SysMLModel


class SysMLParser(Protocol):
    def parse(self, source: str | Path) -> SysMLModel:
        """Parse source material into the neutral L3 model."""
        ...