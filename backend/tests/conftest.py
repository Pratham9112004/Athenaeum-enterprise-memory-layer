"""Test fixtures.

Uses an in-memory SQLite database and overrides the ``get_db`` dependency so tests run
fast and hermetically, without Postgres. The service/repository layers are DB-agnostic,
so this exercises real query paths.
"""

from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base  # imports all models onto the metadata
from app.db.session import get_db
from app.main import app
from tests.fakes import FakeEmbedder, FakeLLM, FakeVectorStore


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def fakes() -> SimpleNamespace:
    return SimpleNamespace(embedder=FakeEmbedder(), store=FakeVectorStore(), llm=FakeLLM())


@pytest.fixture
def rag_client(db_session: Session, fakes: SimpleNamespace) -> Generator[TestClient, None, None]:
    """A client with the AI providers replaced by fakes.

    Upload-triggered ingestion runs synchronously against the same test session and
    fake vector store, so after an upload the document is 'ready' and searchable.
    """
    from app.api.deps import (
        get_embedder_dep,
        get_ingestion_scheduler,
        get_llm_dep,
        get_vector_store_dep,
    )
    from app.services.pipeline import ingest_document

    def _run(document_id: int) -> None:
        ingest_document(
            db_session,
            document_id,
            embedder=fakes.embedder,
            vector_store=fakes.store,
        )

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_embedder_dep] = lambda: fakes.embedder
    app.dependency_overrides[get_vector_store_dep] = lambda: fakes.store
    app.dependency_overrides[get_llm_dep] = lambda: fakes.llm
    app.dependency_overrides[get_ingestion_scheduler] = lambda: _run

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, email: str = "user@example.com") -> dict:
    """Register a fresh user and return an Authorization header."""
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Test-Password-123", "full_name": "Test"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
