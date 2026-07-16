"""Deterministic in-memory fakes for the AI providers.

These let the pipeline, search, and chat be exercised end-to-end without PyTorch,
a ChromaDB server, or an OpenAI key. The fake embedder is a stable bag-of-words
hash so token overlap drives similarity — enough for retrieval ranking to be
meaningful in tests.
"""

from __future__ import annotations

import hashlib
import math
import re

from app.services.vector_store import VectorHit, VectorRecord

_DIM = 64
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _stable_bucket(token: str) -> int:
    return int(hashlib.md5(token.encode()).hexdigest(), 16) % _DIM


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * _DIM
        for token in _TOKEN_RE.findall(text.lower()):
            vec[_stable_bucket(token)] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    return 1.0 - dot  # inputs are unit vectors


class FakeVectorStore:
    def __init__(self) -> None:
        self.records: dict[str, VectorRecord] = {}

    def add(self, records: list[VectorRecord]) -> None:
        for record in records:
            self.records[record.id] = record

    def query(self, embedding: list[float], top_k: int, owner_id: int) -> list[VectorHit]:
        scored = [
            VectorHit(
                id=r.id,
                metadata=r.metadata,
                distance=_cosine_distance(embedding, r.embedding),
                text=r.text,
            )
            for r in self.records.values()
            if r.metadata.get("owner_id") == owner_id
        ]
        scored.sort(key=lambda h: h.distance)
        return scored[:top_k]

    def delete_document(self, document_id: int) -> None:
        self.records = {
            rid: r
            for rid, r in self.records.items()
            if r.metadata.get("document_id") != document_id
        }


class FakeLLM:
    """Returns a canned grounded answer that cites the first source."""

    def __init__(self, configured: bool = True, answer: str | None = None) -> None:
        self._configured = configured
        self._answer = answer
        self.calls: list[dict] = []

    @property
    def is_configured(self) -> bool:
        return self._configured

    def complete(self, system: str, messages: list[dict]) -> str:
        self.calls.append({"system": system, "messages": messages})
        if self._answer is not None:
            return self._answer
        user_turn = messages[-1]["content"] if messages else ""
        if "[1]" in user_turn or "Sources:" in user_turn:
            return "According to the documents, the answer is grounded here [1]."
        return "I don't have that information in your documents."
