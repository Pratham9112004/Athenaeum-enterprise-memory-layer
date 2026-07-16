"""Integration tests for the documents endpoints (upload/list/get/delete)."""

from tests.conftest import auth_headers

DOCS = "/api/v1/documents"


def _upload(
    client,
    headers,
    name="notes.txt",
    content=b"hello world from athenaeum",
    ctype="text/plain",
):
    return client.post(DOCS, files={"file": (name, content, ctype)}, headers=headers)


def test_upload_then_document_becomes_ready(rag_client):
    headers = auth_headers(rag_client)
    resp = _upload(rag_client, headers)
    assert resp.status_code == 202
    doc_id = resp.json()["id"]

    # Ingestion ran synchronously via the fake providers.
    got = rag_client.get(f"{DOCS}/{doc_id}", headers=headers).json()
    assert got["status"] == "ready"
    assert got["chunk_count"] >= 1


def test_list_only_returns_own_documents(rag_client):
    alice = auth_headers(rag_client, "alice@example.com")
    bob = auth_headers(rag_client, "bob@example.com")
    _upload(rag_client, alice)

    assert len(rag_client.get(DOCS, headers=alice).json()) == 1
    assert rag_client.get(DOCS, headers=bob).json() == []


def test_other_user_cannot_get_or_delete(rag_client):
    alice = auth_headers(rag_client, "alice@example.com")
    bob = auth_headers(rag_client, "bob@example.com")
    doc_id = _upload(rag_client, alice).json()["id"]

    assert rag_client.get(f"{DOCS}/{doc_id}", headers=bob).status_code == 404
    assert rag_client.delete(f"{DOCS}/{doc_id}", headers=bob).status_code == 404


def test_delete_removes_document_and_vectors(rag_client, fakes):
    headers = auth_headers(rag_client)
    doc_id = _upload(rag_client, headers).json()["id"]
    assert len(fakes.store.records) >= 1

    resp = rag_client.delete(f"{DOCS}/{doc_id}", headers=headers)
    assert resp.status_code == 204
    assert rag_client.get(f"{DOCS}/{doc_id}", headers=headers).status_code == 404
    # No orphaned vectors left behind.
    assert all(r.metadata["document_id"] != doc_id for r in fakes.store.records.values())


def test_unsupported_type_rejected(rag_client):
    headers = auth_headers(rag_client)
    resp = _upload(rag_client, headers, name="bad.xyz", ctype="application/octet-stream")
    assert resp.status_code == 422


def test_empty_file_rejected(rag_client):
    headers = auth_headers(rag_client)
    resp = _upload(rag_client, headers, content=b"")
    assert resp.status_code == 422


def test_upload_requires_auth(rag_client):
    resp = _upload(rag_client, headers={})
    assert resp.status_code == 401
