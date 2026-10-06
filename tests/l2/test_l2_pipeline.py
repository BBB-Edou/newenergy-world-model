from __future__ import annotations

import json

from l2_modeling import L2Orchestrator, MockLLMClient, UserAnswer
from l2_modeling.demo import _knowledge_state_payload, _requirement_payload, load_demo_document


def _client(state_payload: dict) -> MockLLMClient:
    return MockLLMClient(
        responses=[
            json.dumps(_requirement_payload(), ensure_ascii=False),
            json.dumps(state_payload, ensure_ascii=False),
        ]
    )


def test_requirement_to_modeling_to_verification_is_valid() -> None:
    result = L2Orchestrator(_client(_knowledge_state_payload())).run(load_demo_document())

    assert result.status == "VALID"
    assert len(result.knowledge_state.entities) == 5
    assert result.verification_result.status == "VALID"


def test_orchestrator_returns_questions_when_user_input_is_needed() -> None:
    payload = _knowledge_state_payload()
    payload["attributes"][2]["value"] = None
    result = L2Orchestrator(_client(payload)).run(load_demo_document())

    assert result.status == "NEED_USER_INPUT"
    assert result.questions is not None
    assert any(question.target_id == "battery_capacity" for question in result.questions.questions)


def test_orchestrator_applies_answer_and_revalidates() -> None:
    payload = _knowledge_state_payload()
    payload["attributes"][2]["value"] = None

    def answer_provider(questions):
        question = next(item for item in questions.questions if item.target_id == "battery_capacity")
        return [UserAnswer(question_id=question.question_id, answer="200")]

    result = L2Orchestrator(_client(payload), answer_provider=answer_provider).run(load_demo_document())

    assert result.status == "VALID"
    assert next(item for item in result.knowledge_state.attributes if item.id == "battery_capacity").value == 200

def test_live_test_is_skipped_by_default(capsys) -> None:
    from l2_modeling.live_test import main

    exit_code = main(["examples/renewable_energy/l2/demo_system.md"])

    assert exit_code == 0
    assert "skipped" in capsys.readouterr().out

def test_orchestrator_fails_on_explicit_conflict() -> None:
    payload = _knowledge_state_payload()
    payload["attributes"][5]["value"] = 90
    payload["attributes"][6]["value"] = 20

    result = L2Orchestrator(_client(payload)).run(load_demo_document())

    assert result.status == "FAILED"
    assert result.verification_result.status == "INVALID"
    assert any(issue.issue_type == "conflict" for issue in result.verification_result.issues)