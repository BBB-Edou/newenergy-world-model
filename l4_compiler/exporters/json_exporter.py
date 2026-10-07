"""Deterministic JSON export/import for World Model IR."""

from __future__ import annotations

import json
from pathlib import Path

from l4_compiler.world_model_ir import WorldModel


def export_world_model_json(world_model: WorldModel, output_path: str | Path | None = None) -> str:
    payload = json.dumps(world_model.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    return payload


def load_world_model_json(source: str | Path) -> WorldModel:
    path = Path(source)
    return WorldModel.model_validate_json(path.read_text(encoding="utf-8-sig"))