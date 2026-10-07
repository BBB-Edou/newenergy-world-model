"""Executable Model interface handed from L4 to L5."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from l4_compiler.world_model_ir import Event, WorldModel


class ExecutableModel(ABC):
    def __init__(self, world_model: WorldModel) -> None:
        self.world_model = world_model

    @abstractmethod
    def initialize(self, initial_state: Mapping[str, Any] | None = None) -> None:
        ...

    @abstractmethod
    def step(self, action: Mapping[str, Any] | None = None, inputs: Mapping[str, Any] | None = None) -> None:
        ...

    @abstractmethod
    def apply_event(self, event: Event) -> None:
        ...

    @abstractmethod
    def get_state(self) -> Mapping[str, Any]:
        ...

    @abstractmethod
    def check_constraints(self) -> Mapping[str, bool]:
        ...

    @abstractmethod
    def calculate_metrics(self) -> Mapping[str, Any]:
        ...