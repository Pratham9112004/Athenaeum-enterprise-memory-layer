"""Document business logic: validation, storage, and lifecycle."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.storage import FileStorage, get_storage
from app.services.vector_store import VectorStore, get_vector_store

# Canonical allowlist: extension -> content type. Validation keys off the extension,
# which is more reliable than the browser-supplied MIME type.
ALLOWED_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class DocumentService:
    def __init__(
        self,
        db: Session,
        storage: FileStorage | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.db = db
        self.repo = DocumentRepository(db)
        self.storage = storage or get_storage()
        self.vector_store = vector_store or get_vector_store()

    def list_documents(self, owner_id: int) -> list[Document]:
        return self.repo.list_for_owner(owner_id)

    def get_document(self, document_id: int, owner_id: int) -> Document:
        doc = self.repo.get_for_owner(document_id, owner_id)
        if doc is None:
            raise NotFoundError("Document not found")
        return doc

    def create_document(
        self, *, owner_id: int, filename: str, content_type: str, data: bytes
    ) -> Document:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_TYPES:
            supported = ", ".join(sorted(ALLOWED_TYPES))
            raise ValidationError(
                f"Unsupported file type '{ext or filename}'. Supported: {supported}."
            )
        if len(data) == 0:
            raise ValidationError("The file is empty.")
        if len(data) > settings.max_upload_bytes:
            limit_mb = settings.max_upload_bytes // (1024 * 1024)
            raise ValidationError(f"File exceeds the {limit_mb} MB limit.")

        storage_path = self.storage.save(owner_id, filename, data)
        doc = self.repo.create(
            owner_id=owner_id,
            filename=filename,
            content_type=ALLOWED_TYPES[ext],
            extension=ext.lstrip("."),
            size_bytes=len(data),
            storage_path=storage_path,
        )
        logger.info("Stored document {} ({} bytes) for user {}", doc.id, len(data), owner_id)
        return doc

    def delete_document(self, document_id: int, owner_id: int) -> None:
        doc = self.get_document(document_id, owner_id)

        # Remove vectors FIRST so we never end up with a deleted row but orphaned
        # embeddings still retrievable in the vector store.
        try:
            self.vector_store.delete_document(doc.id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Vector cleanup failed for document {}: {}", doc.id, exc)
            raise

        try:
            self.storage.delete(doc.storage_path)
        except Exception as exc:  # noqa: BLE001
            # File cleanup failure shouldn't block row deletion; log and continue.
            logger.warning("File cleanup failed for document {}: {}", doc.id, exc)

        self.repo.delete(doc)  # cascades chunk rows
        logger.info("Deleted document {} for user {}", document_id, owner_id)
