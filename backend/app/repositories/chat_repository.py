"""Chat session/message data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat import ChatMessage, ChatSession
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    model = ChatSession

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_session_for_owner(self, session_id: int, owner_id: int) -> ChatSession | None:
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.owner_id == owner_id)
            .options(selectinload(ChatSession.messages))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_sessions_for_owner(self, owner_id: int) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.owner_id == owner_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_session(self, *, owner_id: int, title: str) -> ChatSession:
        session = ChatSession(owner_id=owner_id, title=title[:255])
        return self.add(session)

    def add_message(
        self,
        *,
        session: ChatSession,
        role: str,
        content: str,
        citations: list | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session.id, role=role, content=content, citations=citations
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
