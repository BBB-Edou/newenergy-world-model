"""Structured errors for L2 agents."""

from __future__ import annotations


class L2Error(Exception):
    """Base class for L2 modeling errors."""


class AgentOutputError(L2Error):
    """Raised after finite retries fail JSON/Pydantic validation."""

    def __init__(self, agent_name: str, attempts: int, reason: str) -> None:
        self.agent_name = agent_name
        self.attempts = attempts
        self.reason = reason
        super().__init__(f"{agent_name} returned invalid structured output after {attempts} attempt(s): {reason}")