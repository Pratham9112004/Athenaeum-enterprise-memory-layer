"""Ingestion pipeline.

Runs off the request path (FastAPI background task). Transitions a document
uploaded → processing → ready/failed, and on failure records a human-readable reason
and cleans up any partial vectors so nothing is left orphaned.
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import DocumentChunk, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.chunking import chunk_pages
from app.services.embeddings import EmbeddingProvider, get_embedder
from app.services.parsing import parse_document
from app.services.vector_store import VectorRecord, VectorStore, get_vector_store


def _chroma_id(document_id: int, ordinal: int) -> str:
    return f"doc{document_id}-chunk{ordinal}"


def ingest_document(
    db: Session,
    document_id: int,
    *,
    embedder: EmbeddingProvider | None = None,
    vector_store: VectorStore | None = None,
) -> None:
    """Process one document. Idempotent: re-running replaces prior chunks/vectors."""
    embedder = embedder or get_embedder()
    vector_store = vector_store or get_vector_store()
    repo = DocumentRepository(db)

    document = repo.get(document_id)
    if document is None:
        logger.warning("Ingestion skipped: document {} not found", document_id)
        return

    repo.set_status(document, DocumentStatus.PROCESSING.value)
    try:
        parsed = parse_document(document.storage_path, document.extension)
        if parsed.is_empty:
            raise ValueError("No extractable text was found in this file.")

        chunks = chunk_pages(parsed.pages)
        if not chunks:
            raise ValueError("The document produced no chunks.")

        embeddings = embedder.embed([c.text for c in chunks])

        chunk_rows = [
            DocumentChunk(
                document_id=document.id,
                owner_id=document.owner_id,
                ordinal=c.ordinal,
                page=c.page,
                char_start=c.char_start,
                char_end=c.char_end,
                token_count=c.token_count,
                text=c.text,
                chroma_id=_chroma_id(document.id, c.ordinal),
            )
            for c in chunks
        ]
        repo.replace_chunks(document, chunk_rows)  # commits; populates chunk ids

        records = [
            VectorRecord(
                id=row.chroma_id,
                embedding=embeddings[i],
                metadata=_metadata(row),
                text=row.text,
            )
            for i, row in enumerate(chunk_rows)
        ]
        # Replace any stale vectors from a previous run, then add the current set.
        vector_store.delete_document(document.id)
        vector_store.add(records)

        repo.set_status(document, DocumentStatus.READY.value)
        logger.info("Document {} ready: {} chunks indexed", document.id, len(chunk_rows))

    except Exception as exc:  # noqa: BLE001 - any failure marks the doc failed
        logger.exception("Ingestion failed for document {}", document_id)
        try:
            vector_store.delete_document(document_id)  # best-effort cleanup
        except Exception:  # noqa: BLE001
            pass
        repo.set_status(document, DocumentStatus.FAILED.value, error=str(exc))


def _metadata(row: DocumentChunk) -> dict:
    """Chroma metadata (all values must be non-null scalars)."""
    meta: dict[str, int] = {
        "owner_id": row.owner_id,
        "document_id": row.document_id,
        "chunk_id": row.id,
        "ordinal": row.ordinal,
    }
    if row.page is not None:
        meta["page"] = row.page
    return meta


def run_ingestion(document_id: int) -> None:
    """Background-task entrypoint: owns its own DB session."""
    db = SessionLocal()
    try:
        ingest_document(db, document_id)
    finally:
        db.close()
