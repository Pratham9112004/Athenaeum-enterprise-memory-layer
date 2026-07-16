"""Tests for RAG chat: endpoint behavior + pure citation helpers."""

from app.api.deps import get_llm_dep
from app.main import app
from app.services.chat_service import (
    build_sources_block,
    extract_citation_indices,
    map_citations,
)
from app.services.retrieval import RetrievedChunk
from tests.conftest import auth_headers
from tests.fakes import FakeLLM

DOCS = "/api/v1/documents"
CHAT = "/api/v1/chat"

CONTENT = b"The refund policy allows returns within thirty days of purchase with a receipt."


def _upload(client, headers):
    return client.post(DOCS, files={"file": ("policy.txt", CONTENT, "text/plain")}, headers=headers)


def test_chat_answers_with_citations(rag_client):
    headers = auth_headers(rag_client)
    _upload(rag_client, headers)

    resp = rag_client.post(CHAT, json={"message": "What is the refund window?"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"]
    citations = body["message"]["citations"]
    assert citations
    assert citations[0]["document_name"] == "policy.txt"
    assert citations[0]["index"] == 1
    assert citations[0]["snippet"]


def test_chat_continues_a_session(rag_client):
    headers = auth_headers(rag_client)
    _upload(rag_client, headers)
    first = rag_client.post(CHAT, json={"message": "hello"}, headers=headers).json()
    session_id = first["session_id"]

    second = rag_client.post(
        CHAT, json={"message": "and again", "session_id": session_id}, headers=headers
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == session_id

    detail = rag_client.get(f"{CHAT}/sessions/{session_id}", headers=headers).json()
    # two user turns + two assistant turns
    assert len(detail["messages"]) == 4


def test_chat_unconfigured_llm_returns_503(rag_client):
    headers = auth_headers(rag_client)
    _upload(rag_client, headers)
    app.dependency_overrides[get_llm_dep] = lambda: FakeLLM(configured=False)

    resp = rag_client.post(CHAT, json={"message": "hi"}, headers=headers)
    assert resp.status_code == 503


def test_chat_requires_auth(rag_client):
    assert rag_client.post(CHAT, json={"message": "x"}).status_code == 401


def test_session_scoped_to_owner(rag_client):
    alice = auth_headers(rag_client, "alice@example.com")
    bob = auth_headers(rag_client, "bob@example.com")
    _upload(rag_client, alice)
    sid = rag_client.post(CHAT, json={"message": "hi"}, headers=alice).json()["session_id"]

    assert rag_client.get(f"{CHAT}/sessions/{sid}", headers=bob).status_code == 404


# ── pure helper unit tests ───────────────────────────────────────────────────
def _chunk(chunk_id: int, name: str, page: int | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=chunk_id * 10,
        document_name=name,
        page=page,
        text="some source text",
        score=0.9,
        ordinal=0,
    )


def test_extract_citation_indices():
    assert extract_citation_indices("A claim [1] and another [3].") == {1, 3}
    assert extract_citation_indices("no markers here") == set()


def test_build_sources_block_numbers_and_pages():
    block = build_sources_block([_chunk(1, "a.pdf", page=4), _chunk(2, "b.txt")])
    assert "[1] a.pdf, p.4:" in block
    assert "[2] b.txt:" in block


def test_build_sources_block_handles_no_chunks():
    assert "no relevant sources" in build_sources_block([])


def test_map_citations_only_returns_cited():
    chunks = [_chunk(1, "a.pdf"), _chunk(2, "b.txt"), _chunk(3, "c.md")]
    citations = map_citations("Answer grounded in [1] and [3].", chunks)
    assert [c.index for c in citations] == [1, 3]
    assert citations[0].document_name == "a.pdf"
    assert citations[1].document_id == 30
