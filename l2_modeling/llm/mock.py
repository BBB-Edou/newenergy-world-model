"""Small scripted client for deterministic tests and offline demos."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MockLLMClient:
    responses: list[str]
    calls: list[dict[str, object]] = field(default_factory=list)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_format": response_format,
                "max_tokens": max_tokens,
            }
        )
        if not self.responses:
            raise AssertionError("MockLLMClient has no scripted response left")
        return self.responses.pop(0)