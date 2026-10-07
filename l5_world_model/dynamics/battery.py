"""Battery dynamics and WorldModelIR parameter resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass

from l4_compiler.world_model_ir import WorldModel
from l5_world_model.models import SimulationConfig
from scenario_binding.units import UnitAlignmentError, conversion_for


class ModelParameterError(ValueError):
    pass


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


@dataclass(frozen=True, slots=True)
class BatteryParameters:
    state_id: str
    capacity_kwh: float
    max_charge_kw: float
    max_discharge_kw: float
    soc_min_pct: float
    soc_max_pct: float
    charge_efficiency: float
    discharge_efficiency: float


@dataclass(slots=True)
class BatteryModel:
    parameters: BatteryParameters

    def next_soc(self, soc: float, *, charge_kw: float, discharge_kw: float, delta_hours: float) -> float:
        p = self.parameters
        charge_delta = p.charge_efficiency * charge_kw * delta_hours / p.capacity_kwh * 100.0
        discharge_delta = discharge_kw * delta_hours / (p.discharge_efficiency * p.capacity_kwh) * 100.0
        return soc + charge_delta - discharge_delta


def _find_battery_entity(world_model: WorldModel) -> str:
    for entity in world_model.entities:
        if entity.name.strip().lower() == "battery" or entity.entity_type.strip().lower() in {"battery", "storage"}:
            return entity.id
    raise ModelParameterError("WorldModelIR does not define a Battery/storage entity")


def _find_attribute(world_model: WorldModel, owner: str, names: set[str]):
    for attribute in world_model.attributes:
        if attribute.owner == owner and _normalize_name(attribute.name) in names:
            return attribute
    return None


def _to_unit(attribute, target_unit: str, label: str) -> float:
    if attribute.value is None:
        raise ModelParameterError(f"{label} has no value")
    try:
        conversion = conversion_for(attribute.unit, target_unit)
    except UnitAlignmentError as exc:
        raise ModelParameterError(f"{label} unit is invalid: {exc}") from exc
    if conversion is None:
        raise ModelParameterError(f"{label} unit is missing or unknown")
    return float(attribute.value) * conversion.factor


def resolve_battery_parameters(world_model: WorldModel, config: SimulationConfig) -> BatteryParameters:
    owner = _find_battery_entity(world_model)
    state = next((item for item in world_model.states if item.owner == owner and _normalize_name(item.name) == "soc"), None)
    if state is None:
        raise ModelParameterError("WorldModelIR does not define Battery.SOC state")
    capacity = _find_attribute(world_model, owner, {"capacity"})
    max_charge = _find_attribute(world_model, owner, {"max_charge_power", "charge_power_max"})
    max_discharge = _find_attribute(world_model, owner, {"max_discharge_power", "discharge_power_max"})
    soc_min = _find_attribute(world_model, owner, {"soc_min"})
    soc_max = _find_attribute(world_model, owner, {"soc_max"})
    charge_efficiency = _find_attribute(world_model, owner, {"charge_efficiency", "efficiency_charge"})
    discharge_efficiency = _find_attribute(world_model, owner, {"discharge_efficiency", "efficiency_discharge"})
    for attribute, label in ((capacity, "Battery.capacity"), (max_charge, "Battery.max_charge_power"), (max_discharge, "Battery.max_discharge_power"), (soc_min, "Battery.SOC_min"), (soc_max, "Battery.SOC_max")):
        if attribute is None:
            raise ModelParameterError(f"WorldModelIR is missing {label}")
    charge_eff = float(charge_efficiency.value) if charge_efficiency and charge_efficiency.value is not None else config.charge_efficiency
    discharge_eff = float(discharge_efficiency.value) if discharge_efficiency and discharge_efficiency.value is not None else config.discharge_efficiency
    if charge_eff is None or discharge_eff is None:
        raise ModelParameterError("Battery efficiency is missing; provide IR efficiency or explicit SimulationConfig efficiency")
    return BatteryParameters(
        state_id=state.id,
        capacity_kwh=_to_unit(capacity, "kWh", "Battery.capacity"),
        max_charge_kw=_to_unit(max_charge, "kW", "Battery.max_charge_power"),
        max_discharge_kw=_to_unit(max_discharge, "kW", "Battery.max_discharge_power"),
        soc_min_pct=_to_unit(soc_min, "%", "Battery.SOC_min"),
        soc_max_pct=_to_unit(soc_max, "%", "Battery.SOC_max"),
        charge_efficiency=float(charge_eff),
        discharge_efficiency=float(discharge_eff),
    )