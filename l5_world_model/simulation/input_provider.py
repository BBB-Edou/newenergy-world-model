"""L5 input access over the existing ScenarioInputBinding + ScenarioData."""

from __future__ import annotations

from dataclasses import dataclass

from l2_modeling.scenario import ScenarioData, ScenarioInputBinding


class SimulationInputError(ValueError):
    pass


@dataclass(slots=True)
class ScenarioInputProvider:
    binding: ScenarioInputBinding
    scenario: ScenarioData

    def __post_init__(self) -> None:
        if self.binding.status != "READY":
            raise SimulationInputError(f"ScenarioInputBinding is not READY: {self.binding.status}")
        if self.binding.scenario_id != self.scenario.scenario_id:
            raise SimulationInputError("ScenarioInputBinding and ScenarioData scenario_id do not match")
        missing = set(self.binding.variable_mapping) - set(self.scenario.variables)
        if missing:
            raise SimulationInputError(f"ScenarioData is missing mapped variables: {sorted(missing)}")

    def timestamp(self, step_index: int) -> str:
        if step_index < 0 or step_index >= len(self.scenario.time):
            raise SimulationInputError(f"scenario step index out of range: {step_index}")
        return self.scenario.time[step_index]

    def get_inputs(self, step_index: int) -> dict[str, float]:
        timestamp = self.timestamp(step_index)
        del timestamp
        inputs: dict[str, float] = {}
        for model_variable, scenario_variable in sorted(self.binding.variable_mapping.items()):
            values = self.scenario.variables[scenario_variable]
            if step_index >= len(values):
                raise SimulationInputError(f"ScenarioData variable {scenario_variable!r} has no value at step {step_index}")
            raw = values[step_index]
            if raw is None:
                raise SimulationInputError(f"ScenarioData variable {scenario_variable!r} is missing at step {step_index}")
            try:
                numeric = float(raw)
            except (TypeError, ValueError) as exc:
                raise SimulationInputError(f"ScenarioData variable {scenario_variable!r} is not numeric at step {step_index}") from exc
            unit_mapping = self.binding.unit_mapping.get(model_variable)
            factor = unit_mapping.factor if unit_mapping and unit_mapping.factor is not None else 1.0
            inputs[model_variable] = numeric * factor
        return inputs