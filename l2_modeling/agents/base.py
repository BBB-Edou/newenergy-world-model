"""Shared JSON/Pydantic parsing logic for the logical LLM agents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from l2_modeling.errors import AgentOutputError
from l2_modeling.llm import LLMClient

ModelT = TypeVar("ModelT", bound=BaseModel)
PROMPT_DIRECTORY = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(name: str) -> str:
    return (PROMPT_DIRECTORY / name).read_text(encoding="utf-8")


def extract_json_object(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise json.JSONDecodeError("top-level JSON value must be an object", text, start)
    return payload


def call_json_model(
    *,
    client: LLMClient,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    model_type: type[ModelT],
    max_tokens: int = 4096,
) -> ModelT:
    last_reason = "unknown validation error"
    for attempt in range(1, 3):
        raw = client.chat(
            system_prompt,
            user_prompt,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        try:
            return model_type.model_validate(extract_json_object(raw))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_reason = f"{exc.__class__.__name__}: {exc}"
    raise AgentOutputError(agent_name, attempts=2, reason=last_reason)