"""Load a clearly labelled example/demo scenario JSON file as L1 data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common import SourceRef
from l1_data.models import Configuration, RawDataBundle


def load_demo_scenario(path: str | Path) -> RawDataBundle:
    """Load a demo scenario without interpreting its downstream semantics."""

    scenario_path = Path(path).resolve()
    payload: dict[str, Any] = json.loads(scenario_path.read_text(encoding="utf-8-sig"))
    if str(payload.get("metadata", {}).get("data_class", "")).lower() != "example/demo":
        raise ValueError("scenario must be explicitly labelled metadata.data_class = example/demo")

    components = payload.get("components", [])
    if not isinstance(components, list):
        raise ValueError("scenario.components must be a list")

    source = SourceRef(
        source_id=str(payload.get("scenario_id", scenario_path.stem)),
        kind="json_scenario",
        uri=scenario_path.as_uri(),
        metadata={"data_class": "example/demo"},
    )
    configuration = Configuration(
        artifact_id=f"{source.source_id}-configuration",
        name=str(payload.get("name", scenario_path.stem)),
        source=source,
        values={
            "scenario_id": payload.get("scenario_id"),
            "components": components,
            "relations": payload.get("relations", []),
        },
        metadata={"data_class": "example/demo", "status": "placeholder"},
    )
    return RawDataBundle(
        bundle_id=f"{source.source_id}-bundle",
        artifacts=(configuration,),
        source_directory=str(scenario_path.parent),
        metadata={"data_class": "example/demo"},
    )