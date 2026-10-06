"""Compatibility alias for the canonical mock LLM client."""

from l2_modeling.llm.mock import MockLLMClient

MockLLMProvider = MockLLMClient

__all__ = ["MockLLMProvider"]