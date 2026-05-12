from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from app.config import settings

MODEL_ALIASES = {
    "Doubao-Seed-2.0-mini": "doubao-seed-2-0-mini-260215",
    "doubao-seed-2.0-mini": "doubao-seed-2-0-mini-260215",
}


class LLMConfigurationError(RuntimeError):
    pass


class OpenAICompatibleLLMService:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
        if not settings.openai_base_url:
            raise LLMConfigurationError("OPENAI_BASE_URL is not configured.")
        if not settings.llm_model:
            raise LLMConfigurationError("LLM_MODEL is not configured.")

        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.llm_model
        self.model_candidates = self._model_candidates(settings.llm_model)
        self.timeout = settings.llm_timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, model: str, messages: list[dict[str, str]], stream: bool) -> dict:
        return {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "stream": stream,
        }

    async def complete(self, messages: list[dict[str, str]]) -> str:
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for model in self.model_candidates:
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=self._payload(model, messages, stream=False),
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response.status_code == 404:
                        continue
                    raise

        if last_error:
            raise last_error
        raise RuntimeError("No LLM model candidates available.")

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for model in self.model_candidates:
                try:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=self._payload(model, messages, stream=True),
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if not line or not line.startswith("data:"):
                                continue

                            data = line[5:].strip()
                            if data == "[DONE]":
                                return

                            payload = json.loads(data)
                            delta = payload["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        return
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    if exc.response.status_code == 404:
                        continue
                    raise

        if last_error:
            raise last_error
        raise RuntimeError("No LLM model candidates available.")

    def _model_candidates(self, raw_model: str) -> list[str]:
        alias = MODEL_ALIASES.get(raw_model)
        if alias and alias != raw_model:
            return [raw_model, alias]
        return [raw_model]


def get_llm_service() -> OpenAICompatibleLLMService | None:
    if settings.llm_provider in {"openai-compatible", "openai", "ark"}:
        return OpenAICompatibleLLMService()
    return None
