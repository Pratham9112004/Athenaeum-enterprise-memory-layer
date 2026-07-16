"""Integration tests for semantic search."""

from tests.conftest import auth_headers

DOCS = "/api/v1/documents"
SEARCH = "/api/v1/search"

PHOTOSYNTHESIS = (
    b"Photosynthesis converts sunlight, water, and carbon dioxide into glucose "
    b"and oxygen inside the chloroplasts of plant cells."
)
BUDGET = b"The marketing budget for the fourth quarter increased to two million dollars."


def _upload(client, headers, name, content):
    return client.post(DOCS, files={"file": (name, content, "text/plain")}, headers=headers)


def test_search_returns_relevant_scoped_results(rag_client):
    headers = auth_headers(rag_client)
    _upload(rag_client, headers, "bio.txt", PHOTOSYNTHESIS)
    _upload(rag_client, headers, "finance.txt", BUDGET)

    resp = rag_client.post(
        SEARCH, json={"query": "sunlight and glucose in plant cells"}, headers=headers
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results
    top = results[0]
    assert top["document_name"] == "bio.txt"
    assert 0.0 <= top["score"] <= 1.0
    assert top["chunk_id"] and top["snippet"]


def test_search_is_owner_scoped(rag_client):
    alice = auth_headers(rag_client, "alice@example.com")
    bob = auth_headers(rag_client, "bob@example.com")
    _upload(rag_client, alice, "bio.txt", PHOTOSYNTHESIS)

    resp = rag_client.post(SEARCH, json={"query": "sunlight glucose"}, headers=bob)
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_search_requires_auth(rag_client):
    assert rag_client.post(SEARCH, json={"query": "x"}).status_code == 401
