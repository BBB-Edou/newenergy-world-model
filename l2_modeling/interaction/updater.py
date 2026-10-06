"""Deterministic question generation and field-targeted KnowledgeState updates."""

from __future__ import annotations

import json
from typing import Any

from l2_modeling.interaction.schema import Question, QuestionSet, StateUpdateResult, UserAnswer
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.verification import VerificationResult

_TARGET_TYPE_TO_FIELD = {
    "entity": "entities",
    "attribute": "attributes",
    "state": "states",
    "relation": "relations",
    "process": "processes",
    "constraint": "constraints",
    "objective": "objectives",
}


def generate_questions(_state: KnowledgeState, verification: VerificationResult) -> QuestionSet:
    questions: list[Question] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for issue in verification.issues:
        key = (issue.target_type, issue.target_id, issue.target_field)
        if key in seen:
            continue
        seen.add(key)
        if issue.issue_type == "conflict":
            question_type = "conflict"
        elif issue.issue_type == "missing":
            question_type = "missing"
        else:
            question_type = "clarification"
        target_name = f"{issue.target_type or 'knowledge state'} {issue.target_id or ''}".strip()
        field_name = issue.target_field or "information"
        questions.append(
            Question(
                question_id=f"q-{issue.issue_id}",
                question_type=question_type,
                target_type=issue.target_type or "knowledge_state",
                target_id=issue.target_id,
                target_field=issue.target_field,
                question=f"请补充或确认 {target_name} 的 {field_name}。",
                reason=issue.message,
            )
        )
    return QuestionSet(questions=questions)


def _coerce_answer(raw: str, field: str | None) -> Any:
    answer = raw.strip()
    if field in {"inputs", "outputs", "variables"}:
        return [part.strip() for part in answer.replace("，", ",").replace(";", ",").split(",") if part.strip()]
    if field == "direction":
        return answer.lower()
    lowered = answer.lower()
    if lowered in {"none", "null", "unknown", "不明确", "未知"}:
        return None
    try:
        return json.loads(answer)
    except json.JSONDecodeError:
        return answer


def apply_answers(
    state: KnowledgeState,
    answers: list[UserAnswer],
    questions: QuestionSet,
) -> StateUpdateResult:
    data = state.model_dump()
    question_map = {question.question_id: question for question in questions.questions}
    changed_fields: list[str] = []
    warnings: list[str] = []

    for answer in answers:
        question = question_map.get(answer.question_id)
        if question is None:
            warnings.append(f"unknown question_id: {answer.question_id}")
            continue
        if not question.target_id or not question.target_field:
            warnings.append(f"question {answer.question_id} does not target a concrete field")
            continue
        collection_name = _TARGET_TYPE_TO_FIELD.get(question.target_type)
        if collection_name is None:
            warnings.append(f"unsupported target_type: {question.target_type}")
            continue

        target = next((item for item in data[collection_name] if item["id"] == question.target_id), None)
        if target is None:
            warnings.append(f"target not found: {question.target_type}.{question.target_id}")
            continue
        target[question.target_field] = _coerce_answer(answer.answer, question.target_field)
        changed_fields.append(f"{question.target_type}.{question.target_id}.{question.target_field}")

    updated_state = KnowledgeState.model_validate(data)
    return StateUpdateResult(
        updated=bool(changed_fields),
        knowledge_state=updated_state,
        changed_fields=changed_fields,
        warnings=warnings,
    )