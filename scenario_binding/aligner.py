"""Deterministic WorldModelIR <-> ScenarioData input alignment."""

from __future__ import annotations

from l2_modeling.scenario.schema import (
    BindingValidationSummary,
    ScenarioData,
    ScenarioInputBinding,
    TimeAlignment,
    UnitAlignment,
)
from l2_modeling.scenario.validator import parse_time_step, validate_scenario_data
from l4_compiler.world_model_ir import WorldModel
from scenario_binding.units import IncompatibleUnitError, UnknownUnitError, conversion_for


class ScenarioAlignment:
    def align(self, world_model: WorldModel, scenario: ScenarioData) -> ScenarioInputBinding:
        required_inputs = self._required_inputs(world_model)
        variable_mapping: dict[str, str] = {}
        unit_mapping: dict[str, UnitAlignment] = {}
        missing_inputs: list[str] = []
        unit_mismatches: list[str] = []
        semantic_uncertain: list[str] = []
        invalid_inputs: list[str] = []

        if not required_inputs:
            missing_inputs.append("WorldModelIR has no required_inputs or interface variable_ids")

        scenario_validation = validate_scenario_data(scenario, required_variables=())
        if scenario_validation.status == "INVALID":
            invalid_inputs.extend(issue.message for issue in scenario_validation.issues if issue.severity == "error")
        for issue in scenario_validation.issues:
            if issue.target_field == "time_step" and issue.severity != "error":
                missing_inputs.append(issue.message)

        available_variables = set(scenario.variables)
        aliases = scenario.metadata.get("variable_aliases", {})
        if not isinstance(aliases, dict):
            aliases = {}
        used_sources: set[str] = set()
        for required in required_inputs:
            source_variable = self._resolve_variable(required, available_variables, aliases, used_sources)
            if source_variable is None:
                if required in available_variables:
                    source_variable = required
                elif required in aliases and aliases[required] in available_variables:
                    source_variable = str(aliases[required])
                else:
                    for candidate, canonical in aliases.items():
                        if canonical == required and candidate in available_variables:
                            source_variable = str(candidate)
                            break
            if source_variable is None:
                if required not in available_variables:
                    missing_inputs.append(required)
                else:
                    semantic_uncertain.append(required)
                continue
            variable_mapping[required] = source_variable
            used_sources.add(source_variable)

            target_unit = self._target_unit(world_model, required)
            source_unit = scenario.units.get(source_variable)
            try:
                conversion = conversion_for(source_unit, target_unit)
            except UnknownUnitError as exc:
                unit_mismatches.append(str(exc))
                continue
            except IncompatibleUnitError as exc:
                invalid_inputs.append(str(exc))
                continue
            unit_mapping[required] = UnitAlignment(
                source_unit=source_unit,
                target_unit=target_unit,
                conversion=conversion.conversion if conversion else None,
                factor=conversion.factor if conversion else None,
            )
            spec = ScenarioAlignment._contract_spec(world_model, required)
            if spec is not None and spec.data_type.value in {"integer", "float", "any"}:
                if any(
                    value is None or isinstance(value, str)
                    for value in scenario.variables[source_variable]
                ):
                    invalid_inputs.append(f"scenario input {source_variable!r} contains non-numeric values")

        time_mapping, time_mismatch, time_missing, time_invalid = self._align_time(world_model, scenario)
        if time_missing:
            missing_inputs.append(time_missing)
        if time_invalid:
            invalid_inputs.append(time_invalid)

        if invalid_inputs:
            status = "INVALID"
        elif missing_inputs or semantic_uncertain or unit_mismatches:
            status = "NEED_INPUT"
        else:
            status = "READY"

        return ScenarioInputBinding(
            world_model_ir_id=world_model.metadata.ir_id,
            scenario_id=scenario.scenario_id,
            scenario_data=scenario,
            status=status,
            variable_mapping=variable_mapping,
            unit_mapping=unit_mapping,
            time_mapping=time_mapping,
            validation_summary=BindingValidationSummary(
                missing_inputs=sorted(set(missing_inputs)),
                unit_mismatches=sorted(set(unit_mismatches)),
                time_mismatch=time_mismatch,
                semantic_uncertain=sorted(set(semantic_uncertain)),
                invalid_inputs=sorted(set(invalid_inputs)),
            ),
        )

    @staticmethod
    def _required_inputs(world_model: WorldModel) -> list[str]:
        contract = world_model.scenario_input_contract
        if contract is not None and contract.inputs:
            return sorted(spec.name for spec in contract.inputs if spec.required)
        required = set(world_model.metadata.required_inputs)
        for interface in world_model.interfaces:
            required.update(interface.variable_ids)
        return sorted(required)

    @staticmethod
    def _contract_spec(world_model: WorldModel, variable: str):
        contract = world_model.scenario_input_contract
        if contract is None:
            return None
        return next((spec for spec in contract.inputs if spec.name == variable), None)

    @staticmethod
    def _resolve_variable(required: str, available: set[str], aliases: dict, used: set[str]) -> str | None:
        if required in available and required not in used:
            return required
        alias_target = aliases.get(required)
        if isinstance(alias_target, str) and alias_target in available and alias_target not in used:
            return alias_target
        return None

    @staticmethod
    def _target_unit(world_model: WorldModel, variable: str) -> str | None:
        spec = ScenarioAlignment._contract_spec(world_model, variable)
        if spec is not None:
            return spec.unit
        if variable in world_model.metadata.input_units:
            return world_model.metadata.input_units[variable]
        for attribute in world_model.attributes:
            if variable in {attribute.id, attribute.name, attribute.id.removeprefix("attribute-")}:
                return attribute.unit
        return None

    @staticmethod
    def _align_time(world_model: WorldModel, scenario: ScenarioData) -> tuple[TimeAlignment, bool, str | None, str | None]:
        contract = world_model.scenario_input_contract
        simulation = contract.time_requirements if contract is not None else world_model.metadata.simulation
        target_step = None if simulation.time_unit in {None, "abstract"} else f"{simulation.step_size:g}{simulation.time_unit}"
        source_step = scenario.metadata.get("time_step") if isinstance(scenario.metadata.get("time_step"), str) else None
        mapping = TimeAlignment(source_step=source_step, target_step=target_step, conversion=None)
        if source_step is None or target_step is None:
            return mapping, False, "time step is missing on WorldModelIR or ScenarioData", None
        source_minutes = parse_time_step(source_step)
        target_minutes = parse_time_step(target_step)
        if source_minutes is None or target_minutes is None:
            return mapping, False, None, f"unable to parse time steps: {source_step!r} -> {target_step!r}"
        if source_minutes != target_minutes:
            return mapping, True, None, f"time step mismatch: {source_step!r} -> {target_step!r}; no resampling is performed"
        if len(scenario.time) < simulation.horizon:
            return mapping, False, f"insufficient scenario horizon: need {simulation.horizon} steps, got {len(scenario.time)}", None
        return mapping, False, None, None