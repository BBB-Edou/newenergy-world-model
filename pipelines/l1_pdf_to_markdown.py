"""CLI entry point for the isolated PDF -> Markdown L1 stage."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from l1_data.service import main as l1_main


def main(argv: Sequence[str] | None = None) -> int:
    return l1_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())