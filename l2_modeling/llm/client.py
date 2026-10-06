"""Provider-neutral LLM client protocol used by the four logical agents."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Return the model response content as text."""
        ...