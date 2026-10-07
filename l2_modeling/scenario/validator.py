"""Deterministic ScenarioData validation reusing the existing VerificationResult."""

from __future__ import annotations

import math
import re
from datetime import datetime

from l2_modeling.scenario.schema import ScenarioData
from l2_modeling.verification.schema import VerificationIssue, VerificationResult

DEFAULT_REQUIRED_VARIABLES = ("wind_power", "pv_power", "load_power", "electricity_price")
_TIME_RE = re.compile(r"^(?P<hour>\d{1,2}):(?P<minute>\d{2})(?::(?P<second>\d{2}))?$")
_STEP_RE = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>h|hr|hour|hours|m|min|minute|minutes|s|sec|second|seconds|小时|分钟|秒)$", re.IGNORECASE)


def _issue(issues: list[VerificationIssue], *, issue_type: str, severity: str, message: str, target_type: str, target_id: str | None = None, target_field: str | None = None) -> None:
    issues.append(VerificationIssue(issue_id=f"scenario-{len(issues)+1:03d}", severity=severity, issue_type=issue_type, message=message, target_type=target_type, target_id=target_id, target_field=target_field))


def _time_value(value: str) -> float | None:
    match = _TIME_RE.match(value.strip())
    if match:
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        second = int(match.group("second") or 0)
        if 0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60:
            return hour * 60 + minute + second / 60
    try:
        return datetime.fromisoformat(value.strip()).timestamp() / 60
    except ValueError:
        return None


def parse_time_step(value: str | None) -> float | None:
    if not value:
        return None
    match = _STEP_RE.match(value.strip())
    if not match:
        return None
    amount = float(match.group("value"))
    unit = match.group("unit").lower()
    if unit in {"h", "hr", "hour", "hours", "小时"}:
        return amount * 60
    if unit in {"m", "min", "minute", "minutes", "分钟"}:
        return amount
    return amount / 60


def validate_scenario_data(
    scenario: ScenarioData,
    *,
    required_variables: tuple[str, ...] = DEFAULT_REQUIRED_VARIABLES,
) -> VerificationResult:
    issues: list[VerificationIssue] = []
    if not scenario.time:
        _issue(issues, issue_type="missing", severity="warning", message="scenario time column is empty", target_type="scenario", target_id=scenario.scenario_id, target_field="time")
    if not scenario.source.document or not scenario.source.table_id:
        _issue(issues, issue_type="invalid_reference", severity="error", message="scenario source is incomplete", target_type="scenario", target_id=scenario.scenario_id, target_field="source")

    for variable in required_variables:
        if variable not in scenario.variables:
            _issue(issues, issue_type="missing", severity="warning", message=f"required scenario variable {variable!r} is missing", target_type="scenario_variable", target_id=variable, target_field="column")

    for variable, values in scenario.variables.items():
        if len(values) != len(scenario.time):
            _issue(issues, issue_type="invalid_value", severity="error", message=f"variable {variable!r} length does not match time length", target_type="scenario_variable", target_id=variable, target_field="values")
        if not scenario.units.get(variable):
            _issue(issues, issue_type="missing", severity="warning", message=f"unit is not specified for {variable!r}", target_type="scenario_variable", target_id=variable, target_field="unit")
        for row_index, value in enumerate(values):
            if value is None:
                _issue(issues, issue_type="missing", severity="warning", message=f"missing value at row {row_index} for {variable!r}", target_type="scenario_value", target_id=f"{variable}:{row_index}", target_field="value")
            elif isinstance(value, str):
                _issue(issues, issue_type="invalid_type", severity="error", message=f"non-numeric value at row {row_index} for {variable!r}", target_type="scenario_value", target_id=f"{variable}:{row_index}", target_field="value")
            elif isinstance(value, float) and not math.isfinite(value):
                _issue(issues, issue_type="invalid_value", severity="error", message=f"non-finite value at row {row_index} for {variable!r}", target_type="scenario_value", target_id=f"{variable}:{row_index}", target_field="value")

    parsed_times = [_time_value(value) for value in scenario.time]
    if any(value is None for value in parsed_times):
        _issue(issues, issue_type="invalid_value", severity="error", message="scenario contains an invalid time value", target_type="scenario", target_id=scenario.scenario_id, target_field="time")
    else:
        numeric_times = [value for value in parsed_times if value is not None]
        if any(next_value <= value for value, next_value in zip(numeric_times, numeric_times[1:])):
            _issue(issues, issue_type="invalid_value", severity="error", message="scenario time must be strictly increasing", target_type="scenario", target_id=scenario.scenario_id, target_field="time")
        differences = [round(next_value - value, 9) for value, next_value in zip(numeric_times, numeric_times[1:])]
        declared_step = parse_time_step(scenario.metadata.get("time_step") if isinstance(scenario.metadata.get("time_step"), str) else None)
        if declared_step is None:
            _issue(issues, issue_type="missing", severity="warning", message="scenario time_step is not specified", target_type="scenario", target_id=scenario.scenario_id, target_field="time_step")
        elif differences and any(abs(difference - declared_step) > 1e-6 for difference in differences):
            _issue(issues, issue_type="invalid_value", severity="error", message="scenario row interval does not match declared time_step", target_type="scenario", target_id=scenario.scenario_id, target_field="time_step")

    if any(issue.severity == "error" for issue in issues):
        status = "INVALID"
    elif issues:
        status = "NEED_INPUT"
    else:
        status = "VALID"
    return VerificationResult(status=status, issues=issues)