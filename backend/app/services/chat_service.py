"""Chat with documents (RAG).

Retrieves owner-scoped chunks, builds a grounded prompt that numbers each source,
asks the LLM to cite with [n] markers, then maps those markers back to the exact
source chunks. Conversation history is persisted per user.
"""

from __future__ import annotations

import re

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.models.chat import ChatSession, MessageRole
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatMessageRead, ChatResponse, Citation
from app.services.embeddings import EmbeddingProvider
from app.services.llm import LLMProvider, get_llm
from app.services.retrieval import RetrievedChunk, retrieve
from app.services.vector_store import VectorStore

SYSTEM_PROMPT = (
    "You are Athenaeum, an assistant that answers questions about an organization's "
    "internal documents. Answer using ONLY the numbered sources provided. Cite every "
    "claim with its source marker in square brackets, like [1] or [2]. If the sources "
    "do not contain the answer, say you don't have that information — do not invent "
    "anything."
)

_CITATION_RE = re.compile(r"\[(\d+)\]")
_SNIPPET_CHARS = 320


class ChatService:
    def __init__(
        self,
        db: Session,
        embedder: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        llm: LLMProvider | None = None,
    ) -> None:
        self.db = db
        self.repo = ChatRepository(db)
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm = llm or get_llm()

    def answer(self, *, owner_id: int, message: str, session_id: int | None) -> ChatResponse:
        if not self.llm.is_configured:
            raise ServiceUnavailableError(
                f"Chat is unavailable: no API key configured for the '{settings.llm_provider}' LLM provider."
            )

        session = self._resolve_session(owner_id, session_id, message)
        history = self._history_messages(session)

        chunks = retrieve(
            self.db,
            owner_id=owner_id,
            query=message,
            top_k=settings.retrieval_top_k,
            embedder=self.embedder,
            vector_store=self.vector_store,
        )

        user_turn = f"{message}\n\nSources:\n{build_sources_block(chunks)}"
        try:
            answer_text = self.llm.complete(
                SYSTEM_PROMPT, [*history, {"role": "user", "content": user_turn}]
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("LLM completion failed")
            raise ServiceUnavailableError(
                "The language model request failed. Please try again."
            ) from exc

        citations = map_citations(answer_text, chunks)

        self.repo.add_message(session=session, role=MessageRole.USER.value, content=message)
        assistant_msg = self.repo.add_message(
            session=session,
            role=MessageRole.ASSISTANT.value,
            content=answer_text,
            citations=[c.model_dump() for c in citations] or None,
        )

        return ChatResponse(
            session_id=session.id,
            message=ChatMessageRead.model_validate(assistant_msg),
        )

    # ── helpers ──────────────────────────────────────────────────────────────
    def _resolve_session(
        self, owner_id: int, session_id: int | None, first_message: str
    ) -> ChatSession:
        if session_id is not None:
            session = self.repo.get_session_for_owner(session_id, owner_id)
            if session is None:
                raise NotFoundError("Chat session not found")
            return session
        return self.repo.create_session(owner_id=owner_id, title=_title_from(first_message))

    def _history_messages(self, session: ChatSession) -> list[dict]:
        recent = session.messages[-settings.chat_history_limit :]
        return [{"role": m.role, "content": m.content} for m in recent]


# ── pure, unit-testable helpers ──────────────────────────────────────────────
def build_sources_block(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no relevant sources were found in your documents)"
    lines = []
    for index, chunk in enumerate(chunks, start=1):
        location = chunk.document_name
        if chunk.page is not None:
            location += f", p.{chunk.page}"
        lines.append(f"[{index}] {location}: {chunk.text}")
    return "\n\n".join(lines)


def extract_citation_indices(answer: str) -> set[int]:
    return {int(m) for m in _CITATION_RE.findall(answer)}


def map_citations(answer: str, chunks: list[RetrievedChunk]) -> list[Citation]:
    """Resolve the [n] markers in the answer back to their source chunks."""
    cited = extract_citation_indices(answer)
    citations: list[Citation] = []
    for index, chunk in enumerate(chunks, start=1):
        if index in cited:
            citations.append(
                Citation(
                    index=index,
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page=chunk.page,
                    snippet=_snippet(chunk.text),
                )
            )
    return citations


def _snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SNIPPET_CHARS:
        return collapsed
    return collapsed[:_SNIPPET_CHARS].rstrip() + "…"


def _title_from(message: str) -> str:
    words = message.strip().split()
    title = " ".join(words[:8])
    return title or "New chat"
