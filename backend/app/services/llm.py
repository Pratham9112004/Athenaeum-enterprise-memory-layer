"""LLM provider.

An interface plus OpenAI and Gemini implementations, selected via ``settings.llm_provider``.
Each provider's client library is imported lazily and reports whether it's configured, so
the chat service can fail with a clear 503 instead of a stack trace when no API key is set.
Tests inject a fake.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.core.config import settings


class LLMProvider(Protocol):
    @property
    def is_configured(self) -> bool: ...
    def complete(self, system: str, messages: list[dict]) -> str: ...


class OpenAIProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI  # lazy

            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def complete(self, system: str, messages: list[dict]) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, *messages],
            max_tokens=settings.chat_max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


class GeminiProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
        self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None:
            from google import genai  # lazy

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def complete(self, system: str, messages: list[dict]) -> str:
        from google.genai import types  # lazy

        client = self._get_client()

        # Verified against app/models/chat.py: MessageRole.USER = "user",
        # MessageRole.ASSISTANT = "assistant". Gemini has no "assistant" role —
        # its own prior turns are labeled "model" — and takes no "system" role
        # in the turn list at all (passed separately as system_instruction).
        contents = [
            {
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
        ]

        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=settings.chat_max_tokens,
                temperature=0.2,
            ),
        )
        return response.text or ""


@lru_cache
def get_llm() -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "openai":
        return OpenAIProvider()
    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}' "
        "— expected 'openai' or 'gemini'."
    )