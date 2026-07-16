"""Retrieval: embed a query, search the vector store (owner-scoped), and hydrate
hits with their source chunk text and document name from Postgres.

Shared by semantic search (Feature 4) and RAG chat (Feature 5) so both rank and cite
results identically.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.embeddings import EmbeddingProvider, get_embedder
from app.services.vector_store import VectorStore, get_vector_store


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    document_name: str
    page: int | None
    text: str
    score: float
    ordinal: int


def retrieve(
    db: Session,
    *,
    owner_id: int,
    query: str,
    top_k: int,
    embedder: EmbeddingProvider | None = None,
    vector_store: VectorStore | None = None,
) -> list[RetrievedChunk]:
    query = query.strip()
    if not query:
        return []

    embedder = embedder or get_embedder()
    vector_store = vector_store or get_vector_store()

    query_embedding = embedder.embed_one(query)
    hits = vector_store.query(query_embedding, top_k=top_k, owner_id=owner_id)
    if not hits:
        return []

    chunk_ids = [int(h.metadata["chunk_id"]) for h in hits if "chunk_id" in h.metadata]
    chunks = {
        c.id: c
        for c in db.execute(select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))).scalars()
    }
    doc_ids = {c.document_id for c in chunks.values()}
    doc_names = {
        d.id: d.filename
        for d in db.execute(select(Document).where(Document.id.in_(doc_ids))).scalars()
    }

    results: list[RetrievedChunk] = []
    for hit in hits:
        chunk_id = int(hit.metadata.get("chunk_id", -1))
        chunk = chunks.get(chunk_id)
        if chunk is None:  # vector without a live row (defensive)
            continue
        results.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=doc_names.get(chunk.document_id, "Unknown document"),
                page=chunk.page,
                text=chunk.text,
                score=round(hit.relevance, 4),
                ordinal=chunk.ordinal,
            )
        )
    return results
