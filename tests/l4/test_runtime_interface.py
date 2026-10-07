from __future__ import annotations

import inspect

from l4_compiler.runtime import ExecutableModel


def test_executable_model_interface_exposes_l5_methods() -> None:
    expected = {"initialize", "step", "apply_event", "get_state", "check_constraints", "calculate_metrics"}
    assert inspect.isabstract(ExecutableModel)
    assert expected.issubset(set(ExecutableModel.__abstractmethods__))