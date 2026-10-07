from __future__ import annotations

from l2_modeling.scenario import detect_markdown_tables, is_scenario_candidate, scenario_candidates


SCENARIO_MARKDOWN = """<!-- page: 3 -->

| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
| 01:00 | 110 | 0 | 280 | 0.35 |
"""

PARAMETER_MARKDOWN = """| Parameter | Value | Unit |
|---|---:|---|
| Capacity | 200 | kWh |
"""


def test_markdown_table_detection_preserves_page() -> None:
    table = detect_markdown_tables(SCENARIO_MARKDOWN)[0]
    assert table.table_id == "table_01"
    assert table.page == 3
    assert table.headers == ("时间", "风电", "光伏", "负荷", "电价")
    assert table.rows[0] == ("00:00", "120", "0", "300", "0.35")


def test_scenario_candidate_detection_requires_time_and_measure_columns() -> None:
    assert is_scenario_candidate(detect_markdown_tables(SCENARIO_MARKDOWN)[0])
    assert not is_scenario_candidate(detect_markdown_tables(PARAMETER_MARKDOWN)[0])
    assert len(scenario_candidates(SCENARIO_MARKDOWN)) == 1