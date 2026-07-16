"""Embeddings.

An interface plus a sentence-transformers implementation. The heavy library and model
weights are loaded lazily on first use, so importing this module (for tests or
``verify_setup``) never pulls in PyTorch. Tests inject a deterministic fake instead.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.core.config import settings


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    """Embeds text with a sentence-transformers model (default all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self._model = None  # loaded on first use

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy, heavy

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return [v.tolist() for v in vectors]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


@lru_cache
def get_embedder() -> EmbeddingProvider:
    """Cached embedder singleton (loading the model once is expensive)."""
    return SentenceTransformerEmbedder()
