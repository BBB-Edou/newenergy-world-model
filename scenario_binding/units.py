"""Deterministic unit compatibility and conversion rules."""

from __future__ import annotations

from dataclasses import dataclass

_UNIT_ALIASES = {
    "w": "w",
    "kw": "kw",
    "mw": "mw",
    "gw": "gw",
    "wh": "wh",
    "kwh": "kwh",
    "mwh": "mwh",
    "%": "%",
    "percent": "%",
    "cn": "cny/kwh",
    "cny/kwh": "cny/kwh",
    "rmb/kwh": "cny/kwh",
    "yuan/kwh": "cny/kwh",
    "元/kwh": "cny/kwh",
}
_POWER_TO_KW = {"w": 0.001, "kw": 1.0, "mw": 1000.0, "gw": 1_000_000.0}
_ENERGY_TO_KWH = {"wh": 0.001, "kwh": 1.0, "mwh": 1000.0}
_DIMENSIONS = {
    "w": ("power", _POWER_TO_KW),
    "kw": ("power", _POWER_TO_KW),
    "mw": ("power", _POWER_TO_KW),
    "gw": ("power", _POWER_TO_KW),
    "wh": ("energy", _ENERGY_TO_KWH),
    "kwh": ("energy", _ENERGY_TO_KWH),
    "mwh": ("energy", _ENERGY_TO_KWH),
    "%": ("ratio", {"%": 1.0}),
    "cny/kwh": ("price", {"cny/kwh": 1.0}),
}


@dataclass(frozen=True, slots=True)
class UnitConversion:
    source_unit: str
    target_unit: str
    factor: float
    conversion: str | None

    @property
    def compatible(self) -> bool:
        return True


class UnitAlignmentError(ValueError):
    pass


class UnknownUnitError(UnitAlignmentError):
    pass


class IncompatibleUnitError(UnitAlignmentError):
    pass


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    normalized = unit.strip().lower().replace(" ", "")
    if normalized in {"", "unknown", "unspecified", "不明确"}:
        return None
    return _UNIT_ALIASES.get(normalized, normalized)


def conversion_for(source_unit: str | None, target_unit: str | None) -> UnitConversion | None:
    source = normalize_unit(source_unit)
    target = normalize_unit(target_unit)
    if target is None:
        return None
    if source is None:
        raise UnknownUnitError(f"source unit is missing or unknown for target {target}")
    if source == target:
        return UnitConversion(source_unit=source, target_unit=target, factor=1.0, conversion=None)
    if source not in _DIMENSIONS or target not in _DIMENSIONS:
        raise UnknownUnitError(f"unsupported unit conversion: {source} -> {target}")
    source_dimension, source_factors = _DIMENSIONS[source]
    target_dimension, target_factors = _DIMENSIONS[target]
    if source_dimension != target_dimension:
        raise IncompatibleUnitError(f"incompatible units: {source} -> {target}")
    factor = source_factors[source] / target_factors[target]
    return UnitConversion(source_unit=source, target_unit=target, factor=factor, conversion=f"×{factor:g}")