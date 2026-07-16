"""Shared API dependencies."""

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.embeddings import EmbeddingProvider, get_embedder
from app.services.llm import LLMProvider, get_llm
from app.services.pipeline import run_ingestion
from app.services.storage import FileStorage, get_storage
from app.services.vector_store import VectorStore, get_vector_store

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


# ── Provider dependencies ─────────────────────────────────────────────────────
# Thin wrappers around the cached provider singletons. Declaring them as FastAPI
# dependencies lets tests swap in fakes via app.dependency_overrides, exactly like
# the get_db override, without any real ChromaDB / model / OpenAI calls.
def get_embedder_dep() -> EmbeddingProvider:
    return get_embedder()


def get_vector_store_dep() -> VectorStore:
    return get_vector_store()


def get_llm_dep() -> LLMProvider:
    return get_llm()


def get_storage_dep() -> FileStorage:
    return get_storage()


def get_ingestion_scheduler() -> Callable[[int], None]:
    """The function scheduled as a background task after upload."""
    return run_ingestion


EmbedderDep = Annotated[EmbeddingProvider, Depends(get_embedder_dep)]
VectorStoreDep = Annotated[VectorStore, Depends(get_vector_store_dep)]
LLMDep = Annotated[LLMProvider, Depends(get_llm_dep)]
StorageDep = Annotated[FileStorage, Depends(get_storage_dep)]
IngestionScheduler = Annotated[Callable[[int], None], Depends(get_ingestion_scheduler)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Resolve the authenticated user from the Bearer access token."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Not authenticated")
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid or expired token") from exc

    return AuthService(db).get_active_user(int(payload["sub"]))


CurrentUser = Annotated[User, Depends(get_current_user)]
