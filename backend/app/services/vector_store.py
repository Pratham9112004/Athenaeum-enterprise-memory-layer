"""Vector store.

An interface plus a ChromaDB implementation. Retrieval is always owner-scoped via a
metadata filter, so one user can never see another's chunks. chromadb is imported
lazily so the module loads without it; tests use an in-memory fake.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.core.config import settings


@dataclass
class VectorRecord:
    id: str
    embedding: list[float]
    metadata: dict
    text: str


@dataclass
class VectorHit:
    id: str
    metadata: dict
    distance: float
    text: str

    @property
    def relevance(self) -> float:
        """Map cosine distance (0..2) to a 0..1 relevance score."""
        return max(0.0, 1.0 - self.distance)


class VectorStore(Protocol):
    def add(self, records: list[VectorRecord]) -> None: ...
    def query(self, embedding: list[float], top_k: int, owner_id: int) -> list[VectorHit]: ...
    def delete_document(self, document_id: int) -> None: ...


class ChromaVectorStore:
    """Persists embeddings in a ChromaDB server collection."""

    def __init__(self) -> None:
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            import chromadb  # lazy

            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            self._collection = client.get_or_create_collection(
                name=settings.chroma_collection,
                metadata={"hnsw:space": settings.chroma_distance},
            )
        return self._collection

    def add(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        collection = self._get_collection()
        collection.upsert(
            ids=[r.id for r in records],
            embeddings=[r.embedding for r in records],
            metadatas=[r.metadata for r in records],
            documents=[r.text for r in records],
        )

    def query(self, embedding: list[float], top_k: int, owner_id: int) -> list[VectorHit]:
        collection = self._get_collection()
        result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"owner_id": owner_id},
        )
        ids = result["ids"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        documents = result["documents"][0]
        return [
            VectorHit(
                id=ids[i],
                metadata=metadatas[i],
                distance=distances[i],
                text=documents[i],
            )
            for i in range(len(ids))
        ]

    def delete_document(self, document_id: int) -> None:
        collection = self._get_collection()
        collection.delete(where={"document_id": document_id})


@lru_cache
def get_vector_store() -> VectorStore:
    return ChromaVectorStore()
