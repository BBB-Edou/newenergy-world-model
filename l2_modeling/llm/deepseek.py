"""OpenAI-compatible DeepSeek client."""

from __future__ import annotations

import os
from typing import Any

import openai
from openai import OpenAI

from .errors import (
    DeepSeekAuthenticationError,
    DeepSeekRateLimitError,
    DeepSeekRequestError,
    DeepSeekResponseError,
    DeepSeekTimeoutError,
)

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


class DeepSeekClient:
    """Real client for the DeepSeek OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        resolved_key = (api_key or os.getenv("DEEPSEEK_API_KEY") or "").strip()
        if not resolved_key:
            raise DeepSeekAuthenticationError("DEEPSEEK_API_KEY is missing")
        self.model = (model or os.getenv("DEEPSEEK_MODEL") or DEFAULT_MODEL).strip()
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._masked_key = self._mask_key(resolved_key)
        self._client = OpenAI(
            api_key=resolved_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=0,
        )

    def __repr__(self) -> str:
        return f"DeepSeekClient(model={self.model!r}, base_url={self.base_url!r}, api_key={self._masked_key!r})"

    @staticmethod
    def _mask_key(api_key: str) -> str:
        if len(api_key) <= 8:
            return "***"
        return f"{api_key[:4]}...{api_key[-4:]}"

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        request: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format is not None:
            request["response_format"] = response_format
        if max_tokens is not None:
            request["max_tokens"] = max_tokens

        try:
            response = self._client.chat.completions.create(**request)
        except openai.AuthenticationError as exc:
            raise DeepSeekAuthenticationError("DeepSeek authentication failed") from exc
        except openai.APITimeoutError as exc:
            raise DeepSeekTimeoutError(f"DeepSeek request timed out after {self.timeout} seconds") from exc
        except openai.RateLimitError as exc:
            raise DeepSeekRateLimitError("DeepSeek rate limit exceeded") from exc
        except openai.APIConnectionError as exc:
            raise DeepSeekRequestError("DeepSeek network connection failed") from exc
        except openai.APIStatusError as exc:
            status_code = getattr(exc, "status_code", "unknown")
            raise DeepSeekRequestError(f"DeepSeek HTTP error: {status_code}") from exc
        except Exception as exc:
            raise DeepSeekRequestError(f"DeepSeek request failed: {exc.__class__.__name__}") from exc

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise DeepSeekResponseError("DeepSeek returned a malformed response envelope") from exc
        if content is None or not str(content).strip():
            raise DeepSeekResponseError("DeepSeek returned an empty response")
        return str(content)

    def health_check(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False