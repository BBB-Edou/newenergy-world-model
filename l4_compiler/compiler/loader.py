"""SysML JSON loader for L4 compilation."""

from __future__ import annotations

import json
from pathlib import Path

from l3_sysml import SysMLModel


class SysMLLoadError(ValueError):
    pass


def load_sysml(source: SysMLModel | dict | str | Path) -> SysMLModel:
    if isinstance(source, SysMLModel):
        return source
    if isinstance(source, dict):
        try:
            return SysMLModel.model_validate(source)
        except Exception as exc:
            raise SysMLLoadError(f"Invalid SysML dictionary: {exc}") from exc

    path = Path(source)
    if not path.exists() or not path.is_file():
        raise SysMLLoadError(f"SysML file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SysMLLoadError(f"Unable to read SysML JSON: {path} ({exc})") from exc
    try:
        return SysMLModel.model_validate(payload)
    except Exception as exc:
        raise SysMLLoadError(f"Invalid SysML JSON: {path} ({exc})") from exc