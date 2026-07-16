"""Chat (RAG) endpoints."""

from fastapi import APIRouter

from app.api.deps import (
    CurrentUser,
    DbSession,
    EmbedderDep,
    LLMDep,
    VectorStoreDep,
)
from app.core.exceptions import NotFoundError
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionDetail,
    ChatSessionRead,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
    embedder: EmbedderDep,
    vector_store: VectorStoreDep,
    llm: LLMDep,
) -> ChatResponse:
    return ChatService(db, embedder=embedder, vector_store=vector_store, llm=llm).answer(
        owner_id=current_user.id, message=payload.message, session_id=payload.session_id
    )


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(current_user: CurrentUser, db: DbSession) -> list[ChatSessionRead]:
    sessions = ChatRepository(db).list_sessions_for_owner(current_user.id)
    return [ChatSessionRead.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(session_id: int, current_user: CurrentUser, db: DbSession) -> ChatSessionDetail:
    session = ChatRepository(db).get_session_for_owner(session_id, current_user.id)
    if session is None:
        raise NotFoundError("Chat session not found")
    return ChatSessionDetail.model_validate(session)
