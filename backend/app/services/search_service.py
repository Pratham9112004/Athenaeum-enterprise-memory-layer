"""Semantic search business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.search import SearchResponse, SearchResult
from app.services.embeddings import EmbeddingProvider
from app.services.retrieval import retrieve
from app.services.vector_store import VectorStore

_SNIPPET_CHARS = 320


class SearchService:
    def __init__(
        self,
        db: Session,
        embedder: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedder
        self.vector_store = vector_store

    def search(self, *, owner_id: int, query: str, top_k: int | None = None) -> SearchResponse:
        chunks = retrieve(
            self.db,
            owner_id=owner_id,
            query=query,
            top_k=top_k or settings.retrieval_top_k,
            embedder=self.embedder,
            vector_store=self.vector_store,
        )
        results = [
            SearchResult(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_name=c.document_name,
                page=c.page,
                snippet=_snippet(c.text),
                score=c.score,
            )
            for c in chunks
        ]
        return SearchResponse(query=query, results=results)


def _snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SNIPPET_CHARS:
        return collapsed
    return collapsed[:_SNIPPET_CHARS].rstrip() + "…"
