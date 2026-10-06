"""Structured errors raised by L2 LLM clients."""

from __future__ import annotations


class DeepSeekClientError(Exception):
    """Base class for DeepSeek-compatible client failures."""


class DeepSeekAuthenticationError(DeepSeekClientError):
    pass


class DeepSeekRequestError(DeepSeekClientError):
    pass


class DeepSeekRateLimitError(DeepSeekRequestError):
    pass


class DeepSeekTimeoutError(DeepSeekRequestError):
    pass


class DeepSeekResponseError(DeepSeekClientError):
    pass