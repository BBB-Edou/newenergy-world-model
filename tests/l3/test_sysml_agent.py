from __future__ import annotations

from l2_modeling import KnowledgeState, MockLLMClient
from l3_sysml import KnowledgeStateToSysMLMapper, SysMLAgent


def _state() -> KnowledgeState:
    return KnowledgeState(
        entities=[{"id": "wind", "name": "Wind", "entity_type": "renewable_source"}],
        attributes=[{"id": "wind_power", "entity_id": "wind", "name": "rated_power", "value": 100, "unit": "kW"}],
    )


def test_sysml_agent_reuses_shared_llm_protocol_and_parses_model() -> None:
    state = _state()
    expected = KnowledgeStateToSysMLMapper().map(state)
    client = MockLLMClient(responses=[expected.model_dump_json()])

    model = SysMLAgent(client).run(state)

    assert model.bdd.blocks[0].name == "Wind"
    assert client.calls[0]["response_format"] == {"type": "json_object"}
    assert "requirements" in str(client.calls[0]["system_prompt"])
    assert "parametric" in str(client.calls[0]["system_prompt"])