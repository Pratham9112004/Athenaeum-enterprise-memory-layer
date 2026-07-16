"""Document endpoints: upload, list, get, delete."""

from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    IngestionScheduler,
    StorageDep,
    VectorStoreDep,
)
from app.schemas.document import DocumentRead
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(current_user: CurrentUser, db: DbSession) -> list[DocumentRead]:
    docs = DocumentService(db).list_documents(current_user.id)
    return [DocumentRead.model_validate(d) for d in docs]


@router.post("", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    current_user: CurrentUser,
    db: DbSession,
    background: BackgroundTasks,
    storage: StorageDep,
    vector_store: VectorStoreDep,
    schedule_ingestion: IngestionScheduler,
    file: UploadFile = File(...),
) -> DocumentRead:
    data = await file.read()
    doc = DocumentService(db, storage=storage, vector_store=vector_store).create_document(
        owner_id=current_user.id,
        filename=file.filename or "untitled",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    # Parse/chunk/embed off the request path; the client polls for status.
    background.add_task(schedule_ingestion, doc.id)
    return DocumentRead.model_validate(doc)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: int, current_user: CurrentUser, db: DbSession) -> DocumentRead:
    doc = DocumentService(db).get_document(document_id, current_user.id)
    return DocumentRead.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: CurrentUser,
    db: DbSession,
    storage: StorageDep,
    vector_store: VectorStoreDep,
) -> None:
    DocumentService(db, storage=storage, vector_store=vector_store).delete_document(
        document_id, current_user.id
    )
