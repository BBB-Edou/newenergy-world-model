"""Deterministic Markdown table -> ScenarioData builder."""

from __future__ import annotations

import math

from l2_modeling.scenario.markdown_tables import MarkdownTable
from l2_modeling.scenario.schema import DataManifest, ScenarioData

_MISSING_MARKERS = {"", "-", "n/a", "na", "null", "none", "missing", "未提供"}


class ScenarioBuildError(ValueError):
    pass


def parse_scenario_value(raw: str) -> float | int | str | None:
    value = raw.strip()
    if value.lower() in _MISSING_MARKERS:
        return None
    try:
        if any(character in value for character in (".", "e", "E")):
            number = float(value)
            return number if math.isfinite(number) else value
        return int(value)
    except ValueError:
        return value


def build_scenario_data(manifest: DataManifest, table: MarkdownTable) -> ScenarioData:
    header_index = {header: index for index, header in enumerate(table.headers)}
    if manifest.time_column not in header_index:
        raise ScenarioBuildError(f"time column {manifest.time_column!r} not found in {table.table_id}")
    missing_columns = [column for column in manifest.columns if column not in header_index]
    if missing_columns:
        raise ScenarioBuildError(f"scenario columns not found in {table.table_id}: {missing_columns}")

    time_values: list[str] = []
    variables: dict[str, list[float | int | str | None]] = {canonical: [] for canonical in sorted(manifest.columns.values())}
    source_to_canonical = dict(manifest.columns)
    for row in table.rows:
        time_values.append(row[header_index[manifest.time_column]].strip())
        for source_column, canonical in source_to_canonical.items():
            variables[canonical].append(parse_scenario_value(row[header_index[source_column]]))
    return ScenarioData(
        scenario_id=manifest.scenario_id,
        time=time_values,
        variables=variables,
        units={key: manifest.units.get(key) for key in sorted(variables)},
        metadata={"table_id": table.table_id, "time_step": manifest.time_step},
        source=manifest.source,
    )