from __future__ import annotations

import math

import httpx

from app.config import settings
from app.services.vectorizer import VECTOR_DIMENSIONS, VECTOR_MODEL_NAME, text_to_vector


class EmbeddingConfigurationError(RuntimeError):
    pass


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.model = settings.embedding_model
        self.api_key = settings.embedding_api_key or settings.openai_api_key
        self.base_url = (settings.embedding_base_url or settings.openai_base_url).rstrip("/")
        self.timeout = settings.embedding_timeout_seconds
        self.fallback_to_hash = settings.embedding_fallback_to_hash

    @property
    def enabled(self) -> bool:
        return self.provider in {"openai-compatible", "openai", "ark"} and bool(
            self.model and self.api_key and self.base_url
        )

    @property
    def model_name(self) -> str:
        return self.model if self.enabled else VECTOR_MODEL_NAME

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        normalized = [text or "" for text in texts]
        if not normalized:
            return []

        if not self.enabled:
            return [text_to_vector(text) for text in normalized]

        try:
            return self._remote_embeddings(normalized)
        except Exception:
            if not self.fallback_to_hash:
                raise
            return [text_to_vector(text) for text in normalized]

    def _remote_embeddings(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        rows = sorted(data["data"], key=lambda item: item.get("index", 0))
        vectors = [normalize_vector([float(value) for value in row["embedding"]]) for row in rows]
        if len(vectors) != len(texts):
            raise EmbeddingConfigurationError("Embedding response size does not match input size.")
        return vectors


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
