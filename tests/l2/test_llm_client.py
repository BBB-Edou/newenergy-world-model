from __future__ import annotations

from types import SimpleNamespace

import pytest

from l2_modeling.llm import DeepSeekAuthenticationError, DeepSeekClient, DeepSeekResponseError


class _Completions:
    def __init__(self, content):
        self.content = content
        self.requests: list[dict] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))])


def _install_fake_client(client: DeepSeekClient, content) -> _Completions:
    completions = _Completions(content)
    client._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return completions


def test_missing_api_key_raises_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(DeepSeekAuthenticationError):
        DeepSeekClient()


def test_chat_passes_json_response_format() -> None:
    client = DeepSeekClient(api_key="test-key-1234567890", model="configured-model")
    completions = _install_fake_client(client, '{"ok": true}')

    content = client.chat("system", "user", response_format={"type": "json_object"}, max_tokens=123)

    assert content == '{"ok": true}'
    request = completions.requests[0]
    assert request["model"] == "configured-model"
    assert request["response_format"] == {"type": "json_object"}
    assert request["max_tokens"] == 123


def test_empty_response_raises_response_error() -> None:
    client = DeepSeekClient(api_key="test-key-1234567890")
    _install_fake_client(client, None)

    with pytest.raises(DeepSeekResponseError):
        client.chat("system", "user")


def test_repr_masks_api_key() -> None:
    client = DeepSeekClient(api_key="test-key-1234567890")
    assert "test-key-1234567890" not in repr(client)
    assert "test...7890" in repr(client)