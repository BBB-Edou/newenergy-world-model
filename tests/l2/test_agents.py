from __future__ import annotations

import json

import pytest

from l2_modeling import ModelingAgent, MockLLMClient, RawDocument, RequirementAgent
from l2_modeling.demo import _knowledge_state_payload
from l2_modeling.errors import AgentOutputError


def test_requirement_agent_parses_json() -> None:
    client = MockLLMClient(
        responses=[json.dumps({"document_id": "doc-1", "items": [{"id": "wind", "category": "entity", "name": "Wind"}]})]
    )
    result = RequirementAgent(client).run(RawDocument(document_id="doc-1", content="# Wind"))

    assert result.document_id == "doc-1"
    assert result.items[0].id == "wind"
    assert client.calls[0]["response_format"] == {"type": "json_object"}
    assert "JSON" in str(client.calls[0]["system_prompt"])
    assert "{" in str(client.calls[0]["system_prompt"])


def test_modeling_agent_parses_knowledge_state() -> None:
    extraction = RequirementAgent(
        MockLLMClient(responses=[json.dumps({"document_id": "doc-1", "items": []})])
    ).run(RawDocument(document_id="doc-1", content="demo"))
    client = MockLLMClient(responses=[json.dumps(_knowledge_state_payload())])

    state = ModelingAgent(client).run(extraction)

    assert len(state.entities) == 5
    assert state.objectives[0].direction == "minimize"


def test_invalid_json_retries_once_then_raises() -> None:
    client = MockLLMClient(responses=["not json", "still not json"])

    with pytest.raises(AgentOutputError) as exc_info:
        RequirementAgent(client).run(RawDocument(document_id="doc-1", content="demo"))

    assert exc_info.value.attempts == 2
    assert len(client.calls) == 2