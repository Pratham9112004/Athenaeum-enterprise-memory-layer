"""Pipeline tests: ingest_document against a real (SQLite) session + fakes."""

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.user import User
from app.services.pipeline import ingest_document


def _make_user(db) -> User:
    user = User(email="owner@example.com", hashed_password="x", full_name="Owner")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_document(db, owner_id: int, storage_path: str, extension: str) -> Document:
    doc = Document(
        owner_id=owner_id,
        filename=f"file.{extension}",
        content_type="text/plain",
        extension=extension,
        size_bytes=123,
        storage_path=storage_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_ingest_reaches_ready_and_indexes_chunks(db_session, fakes, tmp_path):
    path = tmp_path / "doc.txt"
    path.write_text(" ".join(f"word{i}" for i in range(200)), encoding="utf-8")
    user = _make_user(db_session)
    doc = _make_document(db_session, user.id, str(path), "txt")

    ingest_document(db_session, doc.id, embedder=fakes.embedder, vector_store=fakes.store)

    db_session.refresh(doc)
    assert doc.status == DocumentStatus.READY.value
    assert doc.chunk_count > 0
    assert doc.error is None

    chunks = db_session.query(DocumentChunk).filter_by(document_id=doc.id).all()
    assert len(chunks) == doc.chunk_count
    # Every chunk has a matching vector in the store, scoped to the owner.
    assert len(fakes.store.records) == len(chunks)
    for record in fakes.store.records.values():
        assert record.metadata["owner_id"] == user.id
        assert record.metadata["document_id"] == doc.id


def test_ingest_marks_empty_file_failed(db_session, fakes, tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("   ", encoding="utf-8")
    user = _make_user(db_session)
    doc = _make_document(db_session, user.id, str(path), "txt")

    ingest_document(db_session, doc.id, embedder=fakes.embedder, vector_store=fakes.store)

    db_session.refresh(doc)
    assert doc.status == DocumentStatus.FAILED.value
    assert doc.error
    assert len(fakes.store.records) == 0


def test_ingest_is_idempotent(db_session, fakes, tmp_path):
    path = tmp_path / "doc.txt"
    path.write_text("alpha beta gamma delta epsilon", encoding="utf-8")
    user = _make_user(db_session)
    doc = _make_document(db_session, user.id, str(path), "txt")

    ingest_document(db_session, doc.id, embedder=fakes.embedder, vector_store=fakes.store)
    first = doc.chunk_count
    ingest_document(db_session, doc.id, embedder=fakes.embedder, vector_store=fakes.store)
    db_session.refresh(doc)

    assert doc.chunk_count == first
    assert len(fakes.store.records) == first  # no duplicate vectors
