"""Deterministic ScenarioData -> CSV exporter."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from l2_modeling.scenario.schema import ScenarioData

_PREFERRED_ORDER = ("wind_power", "pv_power", "load_power", "electricity_price")


def _ordered_variables(scenario: ScenarioData) -> list[str]:
    preferred = [name for name in _PREFERRED_ORDER if name in scenario.variables]
    remaining = sorted(name for name in scenario.variables if name not in preferred)
    return preferred + remaining


def export_scenario_csv(scenario: ScenarioData, output_path: str | Path | None = None) -> str:
    variables = _ordered_variables(scenario)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["timestamp", *variables])
    for row_index, timestamp in enumerate(scenario.time):
        row: list[object] = [timestamp]
        for variable in variables:
            value = scenario.variables[variable][row_index] if row_index < len(scenario.variables[variable]) else None
            row.append("missing" if value is None else value)
        writer.writerow(row)
    content = buffer.getvalue()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return content