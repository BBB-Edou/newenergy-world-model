from __future__ import annotations

import json

from l2_modeling import MockLLMClient, RawDocument
from l2_modeling.scenario import ScenarioDataExtractor


MARKDOWN = """<!-- page: 2 -->
| 时间 | 风电 | 光伏 | 负荷 | 电价 |
|---|---:|---:|---:|---:|
| 00:00 | 120 | 0 | 300 | 0.35 |
"""


def test_extractor_uses_llm_for_semantics_and_keeps_table_source() -> None:
    manifest = {
        "scenario_id": "case-1",
        "table_id": "table_01",
        "time_column": "时间",
        "columns": {"风电": "wind_power", "光伏": "pv_power", "负荷": "load_power", "电价": "electricity_price"},
        "units": {"wind_power": "kW", "pv_power": "kW", "load_power": "kW", "electricity_price": "CNY/kWh"},
        "time_step": "1h",
        "source": {"document": "ignored.md", "table_id": "table_01", "page": None},
    }
    client = MockLLMClient(responses=[json.dumps({"document_id": "doc", "manifests": [manifest]})])

    extraction = ScenarioDataExtractor(client).extract(RawDocument(document_id="doc", content=MARKDOWN, filename="case.pdf"))

    result = extraction.manifests[0]
    assert result.columns["风电"] == "wind_power"
    assert result.units["electricity_price"] == "CNY/kWh"
    assert result.source.document == "case.pdf"
    assert result.source.page == 2
    assert len(client.calls) == 1