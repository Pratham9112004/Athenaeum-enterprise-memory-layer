"""Document + chunk data access."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_for_owner(self, owner_id: int) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_for_owner(self, document_id: int, owner_id: int) -> Document | None:
        stmt = select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(
        self,
        *,
        owner_id: int,
        filename: str,
        content_type: str,
        extension: str,
        size_bytes: int,
        storage_path: str,
    ) -> Document:
        doc = Document(
            owner_id=owner_id,
            filename=filename,
            content_type=content_type,
            extension=extension,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        return self.add(doc)

    def set_status(self, document: Document, status: str, *, error: str | None = None) -> Document:
        document.status = status
        document.error = error
        self.db.commit()
        self.db.refresh(document)
        return document

    # ── Chunks ───────────────────────────────────────────────────────────────
    def replace_chunks(self, document: Document, chunks: list[DocumentChunk]) -> None:
        """Delete any existing chunks for the document and insert the new set."""
        self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        self.db.add_all(chunks)
        document.chunk_count = len(chunks)
        self.db.commit()

    def get_chunks_by_ids(self, chunk_ids: list[int]) -> list[DocumentChunk]:
        if not chunk_ids:
            return []
        stmt = select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
        return list(self.db.execute(stmt).scalars().all())
