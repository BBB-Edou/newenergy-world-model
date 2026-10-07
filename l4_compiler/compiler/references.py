"""Reference resolution shared by L4 mapping modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReferenceResolver:
    _ids: dict[str, str] = field(default_factory=dict)
    _owners: dict[str, str | None] = field(default_factory=dict)
    _units: dict[str, str | None] = field(default_factory=dict)

    def register(self, source_id: str, ir_id: str, *, owner: str | None = None, unit: str | None = None) -> None:
        self._ids[source_id] = ir_id
        self._ids[ir_id] = ir_id
        self._owners[source_id] = owner
        self._owners[ir_id] = owner
        self._units[source_id] = unit
        self._units[ir_id] = unit

    def resolve(self, source_id: str) -> str:
        return self._ids.get(source_id, source_id)

    def resolved_list(self, source_ids: list[str]) -> list[str]:
        return sorted({self.resolve(source_id) for source_id in source_ids})

    def owner_of(self, source_id: str) -> str | None:
        return self._owners.get(source_id, self._owners.get(self.resolve(source_id)))

    def unit_of(self, source_id: str) -> str | None:
        return self._units.get(source_id, self._units.get(self.resolve(source_id)))
