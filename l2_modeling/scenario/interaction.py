"""ScenarioData question generation using the existing interaction schemas."""

from __future__ import annotations

import json

from l2_modeling.interaction.schema import Question, QuestionSet, UserAnswer
from l2_modeling.scenario.schema import DataManifest, ScenarioData, ScenarioUpdateResult
from l2_modeling.verification.schema import VerificationResult


def generate_scenario_questions(verification: VerificationResult) -> QuestionSet:
    questions: list[Question] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for issue in verification.issues:
        key = (issue.target_type, issue.target_id, issue.target_field)
        if key in seen:
            continue
        seen.add(key)
        question_type = "missing" if issue.issue_type == "missing" else "clarification"
        questions.append(
            Question(
                question_id=f"scenario-q-{len(questions)+1:03d}",
                question_type=question_type,
                target_type=issue.target_type or "scenario",
                target_id=issue.target_id,
                target_field=issue.target_field,
                question=f"请补充或确认 {issue.target_type} {issue.target_id or ''} 的 {issue.target_field or '信息'}。",
                reason=issue.message,
            )
        )
    return QuestionSet(questions=questions)


def _coerce_value(raw: str) -> float | int | str:
    text = raw.strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def apply_scenario_answers(
    scenario: ScenarioData,
    manifest: DataManifest,
    answers: list[UserAnswer],
    questions: QuestionSet,
) -> ScenarioUpdateResult:
    scenario_data = scenario.model_dump()
    manifest_data = manifest.model_dump()
    question_map = {question.question_id: question for question in questions.questions}
    changed_fields: list[str] = []
    warnings: list[str] = []

    for answer in answers:
        question = question_map.get(answer.question_id)
        if question is None:
            warnings.append(f"unknown question_id: {answer.question_id}")
            continue
        if question.target_type == "scenario_variable" and question.target_field == "unit" and question.target_id:
            unit = answer.answer.strip()
            scenario_data["units"][question.target_id] = unit
            manifest_data["units"][question.target_id] = unit
            changed_fields.append(f"scenario_variable.{question.target_id}.unit")
        elif question.target_type == "scenario_value" and question.target_field == "value" and question.target_id:
            try:
                variable, row_text = question.target_id.rsplit(":", maxsplit=1)
                row_index = int(row_text)
            except ValueError:
                warnings.append(f"invalid scenario value target: {question.target_id}")
                continue
            scenario_data["variables"][variable][row_index] = _coerce_value(answer.answer)
            changed_fields.append(f"scenario_value.{variable}.{row_index}.value")
        else:
            warnings.append(f"unsupported scenario target: {question.target_type}.{question.target_id}.{question.target_field}")

    return ScenarioUpdateResult(
        updated=bool(changed_fields),
        scenario_data=ScenarioData.model_validate(scenario_data),
        data_manifest=DataManifest.model_validate(manifest_data),
        changed_fields=changed_fields,
        warnings=warnings,
    )