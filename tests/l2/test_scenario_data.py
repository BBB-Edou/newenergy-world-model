from __future__ import annotations

from l2_modeling.scenario import (
    DataManifest,
    ScenarioData,
    ScenarioSource,
    build_scenario_data,
    detect_markdown_tables,
    export_scenario_csv,
    validate_scenario_data,
)


MARKDOWN = """<!-- page: 5 -->
| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
| 01:00 | 110 | 0 | 280 | 0.35 |
| 02:00 | 100 | 0 | 270 | 0.35 |
"""


def _manifest() -> DataManifest:
    return DataManifest(
        scenario_id="case-1",
        table_id="table_01",
        time_column="时间",
        columns={"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power", "电价": "electricity_price"},
        units={"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
        time_step="1h",
        source=ScenarioSource(document="case.pdf", table_id="table_01", page=5),
    )


def _scenario(markdown: str = MARKDOWN, manifest: DataManifest | None = None) -> ScenarioData:
    table = detect_markdown_tables(markdown)[0]
    return build_scenario_data(manifest or _manifest(), table)


def test_builder_preserves_values_and_units() -> None:
    scenario = _scenario()
    assert scenario.time == ["00:00", "01:00", "02:00"]
    assert scenario.variables["wind_power"] == [120, 110, 100]
    assert scenario.variables["pv_power"] == [0, 0, 0]
    assert scenario.units["electricity_price"] == "CNY/kWh"
    assert scenario.source.table_id == "table_01"


def test_valid_scenario_passes() -> None:
    assert validate_scenario_data(_scenario()).status == "VALID"


def test_missing_unit_requires_input() -> None:
    manifest = _manifest().model_copy(update={"units": {"wind_power": "kW", "pv_power": "kW", "load_power": "kW"}})
    result = validate_scenario_data(_scenario(manifest=manifest))
    assert result.status == "NEED_INPUT"
    assert any(issue.target_id == "electricity_price" and issue.target_field == "unit" for issue in result.issues)


def test_missing_value_requires_input_and_csv_marks_missing() -> None:
    markdown = MARKDOWN.replace("| 01:00 | 110 |", "| 01:00 | - |")
    scenario = _scenario(markdown)
    result = validate_scenario_data(scenario)
    assert result.status == "NEED_INPUT"
    assert "missing" in export_scenario_csv(scenario)
    assert scenario.variables["wind_power"][1] is None


def test_non_numeric_value_is_invalid() -> None:
    markdown = MARKDOWN.replace("| 01:00 | 110 |", "| 01:00 | bad |")
    result = validate_scenario_data(_scenario(markdown))
    assert result.status == "INVALID"
    assert any(issue.issue_type == "invalid_type" for issue in result.issues)


def test_missing_required_column_requires_input() -> None:
    markdown = """| 时间 | 风电 | 光伏 | 负荷 |
|---|---:|---:|---:|
| 00:00 | 120 | 0 | 300 |
"""
    manifest = _manifest().model_copy(update={"columns": {"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power"}})
    result = validate_scenario_data(_scenario(markdown, manifest))
    assert result.status == "NEED_INPUT"
    assert any(issue.target_id == "electricity_price" for issue in result.issues)


def test_time_step_mismatch_is_invalid() -> None:
    markdown = """| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
| 02:00 | 110 | 0 | 280 | 0.35 |
"""
    result = validate_scenario_data(_scenario(markdown))
    assert result.status == "INVALID"
    assert any(issue.target_field == "time_step" for issue in result.issues)


def test_csv_export_is_deterministic() -> None:
    scenario = _scenario()
    first = export_scenario_csv(scenario)
    second = export_scenario_csv(scenario)
    assert first == second
    assert first.startswith("timestamp,wind_power,pv_power,load_power,electricity_price\n")