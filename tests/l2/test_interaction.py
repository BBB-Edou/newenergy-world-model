from __future__ import annotations

from l2_modeling import Attribute, Entity, KnowledgeState, MockLLMClient, UserAnswer, UserInteractionAgent, VerificationAgent


def _state() -> KnowledgeState:
    return KnowledgeState(
        entities=[Entity(id="battery", name="Battery", entity_type="storage")],
        attributes=[Attribute(id="capacity", entity_id="battery", name="capacity", value=None)],
    )


def test_question_generation_targets_missing_field() -> None:
    state = _state()
    agent = UserInteractionAgent(MockLLMClient([]))
    questions = agent.generate_questions(state, VerificationAgent().verify(state))

    assert len(questions.questions) == 1
    assert questions.questions[0].target_type == "attribute"
    assert questions.questions[0].target_id == "capacity"
    assert questions.questions[0].target_field == "value"


def test_apply_answers_updates_only_targeted_field() -> None:
    state = _state()
    agent = UserInteractionAgent(MockLLMClient([]))
    verification = VerificationAgent().verify(state)
    questions = agent.generate_questions(state, verification)
    question_id = questions.questions[0].question_id

    update = agent.apply_answers(state, [UserAnswer(question_id=question_id, answer="200")])

    assert update.updated
    assert update.knowledge_state.attributes[0].value == 200
    assert update.changed_fields == ["attribute.capacity.value"]
    assert VerificationAgent().verify(update.knowledge_state).status == "VALID"


def test_apply_answers_reports_unknown_question() -> None:
    state = _state()
    agent = UserInteractionAgent(MockLLMClient([]))

    update = agent.apply_answers(state, [UserAnswer(question_id="unknown", answer="1")])

    assert not update.updated
    assert update.warnings == ["unknown question_id: unknown"]