# Athenaeum — Architecture

Enterprise Memory Layer. Stores an organization's internal knowledge and answers
natural-language questions with citations back to the exact source chunks.

---

## 1. High-level architecture

```
                                  ┌─────────────────────────────┐
                                  │        Browser (SPA)        │
                                  │   React + Vite + Tailwind   │
                                  └──────────────┬──────────────┘
                                                 │ HTTPS (JSON)
                                                 │ access token in memory
                                                 │ refresh token in httpOnly cookie
                                  ┌──────────────▼──────────────┐
                                  │        FastAPI (API)        │
                                  │  ┌───────────────────────┐  │
                                  │  │  API layer (routers)  │  │  request/response, auth guards
                                  │  ├───────────────────────┤  │
                                  │  │   Service layer       │  │  business logic (no FastAPI/ORM leak)
                                  │  ├───────────────────────┤  │
                                  │  │  Repository layer     │  │  data access (SQLAlchemy)
                                  │  └───────────────────────┘  │
                                  └───┬───────────────┬─────────┘
                                      │               │
                       ┌──────────────▼───┐    ┌──────▼───────────────┐
                       │   PostgreSQL     │    │      ChromaDB        │
                       │  users, docs,    │    │  vector store        │
                       │  chunks (meta),  │    │  (chunk embeddings   │
                       │  chat sessions   │    │   + metadata)        │
                       └──────────────────┘    └──────────────────────┘
                                      │
                       ┌──────────────▼──────────────────────────────┐
                       │  AI providers (swappable via interface)      │
                       │  Embeddings: sentence-transformers (local)   │
                       │  LLM: OpenAI (MVP) → Ollama (post-MVP)       │
                       └─────────────────────────────────────────────┘
```

Two decoupled paths:

- **Ingestion path** (write): upload → parse → chunk → embed → persist. Runs in the
  background so the request returns immediately and heavy work never blocks the API.
- **Query path** (read): embed query → vector search → build prompt → LLM → cite.

Decoupling them means we can later move ingestion onto Celery/Redis workers, or S3
storage, without touching the query path or the API contract.

---

## 2. Backend folder structure (Clean Architecture)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory, middleware, router mount, lifespan
│   ├── core/
│   │   ├── config.py           # pydantic-settings; all secrets via env
│   │   ├── security.py         # bcrypt (direct) + JWT encode/decode
│   │   ├── logging.py          # Loguru setup
│   │   └── exceptions.py       # domain exceptions + FastAPI handlers
│   ├── db/
│   │   ├── base.py             # Declarative Base + imports every model (for Alembic)
│   │   └── session.py          # engine, SessionLocal, get_db dependency
│   ├── models/                 # SQLAlchemy ORM models (DB shape)
│   │   └── user.py
│   ├── schemas/                # Pydantic models (API shape) — never leak ORM to clients
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── token.py
│   ├── repositories/           # data access; the ONLY layer that talks to the ORM
│   │   ├── base.py
│   │   └── user_repository.py
│   ├── services/               # business logic; pure-ish, unit-testable, no FastAPI
│   │   └── auth_service.py
│   └── api/
│       ├── deps.py             # shared dependencies (get_db, get_current_user)
│       └── v1/
│           ├── router.py       # aggregates all v1 endpoint routers
│           └── endpoints/
│               ├── health.py
│               └── auth.py
├── alembic/                    # migrations; env.py imports ALL models (critical)
├── scripts/verify_setup.py     # imports everything, asserts wiring, checks migrations
├── tests/                      # pytest, service-layer + auth coverage
├── requirements.txt            # one deliberately-resolved dependency set
├── pyproject.toml              # Black + Ruff config
├── alembic.ini
└── Dockerfile
```

**Dependency rule:** dependencies point inward. `api → services → repositories → db`.
Services depend on repository *interfaces*, receive a DB session, and contain no HTTP
or SQL. This is what makes the business logic testable without spinning up FastAPI or
Postgres, and what lets us swap the LLM provider or add RBAC later without a rewrite.

---

## 3. Frontend folder structure

```
frontend/src/
├── main.tsx                    # entry; mounts <App/> inside <AuthProvider/>
├── App.tsx                     # React Router routes + guards
├── index.css                   # Tailwind layers + font faces + base tokens
├── lib/
│   └── api.ts                  # axios instance; attaches access token; refresh-on-401
├── context/
│   └── AuthContext.tsx         # access token in memory + silent refresh
├── hooks/
│   └── useAuth.ts
├── components/
│   ├── ProtectedRoute.tsx      # redirects to /login when unauthenticated
│   ├── layout/AppShell.tsx     # sidebar + top bar, the authenticated frame
│   └── ui/                     # Button, Input, Field, Alert, Badge, Spinner
└── pages/
    ├── Login.tsx
    ├── Register.tsx
    └── Dashboard.tsx
```

- **Routing:** React Router. Public routes (`/login`, `/register`) and guarded routes
  (everything else) wrapped by `ProtectedRoute`.
- **State:** local state + a single `AuthContext` for the session. No global store is
  needed for the MVP; server state is fetched per-view. (React Query is a reasonable
  add later if server-state caching grows.)
- **Auth storage tradeoff:** the **access token lives in memory only** (React state),
  so an XSS payload can't read a token from `localStorage`. The **refresh token is an
  httpOnly cookie** the JS never sees. On load / on 401 we silently call `/auth/refresh`
  to mint a new access token. Cost: a refresh round-trip on hard reload. Worth it.

---

## 4. Request flow — a chat/RAG query (Feature 5)

```
User types question in Chat UI
  → POST /api/v1/chat  { message, session_id }  (Authorization: Bearer <access>)
      → auth guard resolves current user
      → ChatService.answer(user, message):
          1. embed(message)                         # sentence-transformers
          2. vector_store.search(embedding, k, owner=user.id)   # ChromaDB, owner-scoped
          3. fetch chunk metadata from Postgres for the hits
          4. build_prompt(question, retrieved_chunks)
          5. llm.complete(prompt)                   # OpenAI provider (swappable)
          6. map answer spans → citations (doc_id, chunk_id, page, snippet)
      → response: { answer, citations[] }
  → UI renders answer with clickable [1][2] chips → deep-link to source chunk
```

Retrieval is **owner-scoped in the vector query itself** (metadata filter on
`owner_id`), so one user can never retrieve another user's chunks. RBAC/tenant scoping
later becomes an additional filter, not a new code path.

---

## 5. Data flow — document ingestion (Features 2–3)

```
Upload (multipart) → POST /api/v1/documents
  → save file to storage (local disk MVP; S3 later)
  → INSERT documents row (status = "uploaded", owner_id)
  → schedule background task, return 202 + document row
        Background pipeline (status transitions: uploaded → processing → ready/failed)
          1. parse    (PyMuPDF / python-docx / plain text)  → raw text
          2. chunk    (token-aware windows w/ overlap)       → [chunk...]
          3. embed    (all-MiniLM-L6-v2, batched)            → [vector...]
          4. store    vectors + metadata in ChromaDB
                      chunk records (text, ordinal, page, doc_id) in Postgres
          5. mark document "ready" (or "failed" + error on exception)
  → UI polls GET /api/v1/documents and updates status badges
```

Postgres is the **source of truth** for chunk text and provenance; ChromaDB holds the
vectors and a metadata copy for filtering. Keeping chunk text in Postgres means
citations render exact source text even if we later rebuild/repoint the vector index.

---

## 6. Database schema

**PostgreSQL (relational, source of truth):**

| Table            | Purpose                                                                 |
|------------------|-------------------------------------------------------------------------|
| `users`          | id, email (unique), hashed_password, full_name, is_active, timestamps   |
| `documents`      | id, owner_id→users, filename, mime_type, size_bytes, storage_path, status, error, timestamps |
| `document_chunks`| id, document_id→documents, owner_id, ordinal, page, text, token_count, chroma_id, created_at |
| `chat_sessions`  | id, owner_id→users, title, timestamps (Feature 5)                        |
| `chat_messages`  | id, session_id→chat_sessions, role, content, citations(jsonb) (Feature 5)|

**ChromaDB (vectors):** one collection; each record = one chunk embedding, id ==
`document_chunks.chroma_id`, metadata `{ owner_id, document_id, chunk_id, page }`.

**Split rationale:** relational integrity, provenance, and access control belong in
Postgres (joins, foreign keys, transactions). Approximate-nearest-neighbour search over
384-dim vectors belongs in a purpose-built vector store. Neither does the other's job
well, so we use both and let Postgres own the truth.

---

## 7. Why this suits an enterprise application

- **Swappable LLM provider.** Services depend on an `LLMProvider` interface, not on
  `openai` directly. Adding Ollama = one new adapter, zero changes to the RAG logic.
- **Addable RBAC / multi-tenancy.** Every row is already `owner_id`-scoped and retrieval
  filters on it. Roles/tenants become an extra column + filter, not a redesign.
- **Ingestion decoupled from query.** Heavy work runs off the request path (background
  tasks now, Celery/Redis workers later) so uploads never degrade query latency.
- **Testable core.** Business logic sits behind interfaces with no framework coupling,
  so the service layer is unit-tested without a live DB or HTTP server.
- **Provenance-first.** Chunk text + source live in Postgres, making citations exact and
  auditable — the property that separates a serious RAG product from a demo.

---

## 8. Implementation notes (Features 2–5)

These record where the built implementation makes a concrete choice or diverges from the
original brief. Where the brief and this document disagreed, this document won.

- **Document status vocabulary.** Lifecycle is `uploaded → processing → ready/failed`
  (§ above and the frontend `StatusBadge`). The Feature-3 brief called the initial state
  `pending`; we use `uploaded` to stay consistent with this doc and the existing UI. This
  is the only intentional naming divergence.
- **Provider interfaces + lazy imports.** `EmbeddingProvider`, `VectorStore`, and
  `LLMProvider` are Protocols with a concrete adapter each (sentence-transformers,
  ChromaDB, OpenAI). The heavy libraries are imported *inside* the adapters' methods, so
  importing the app (for `verify_setup.py` or tests) never pulls in PyTorch/Chroma/OpenAI.
  Endpoints resolve providers through FastAPI dependencies, so tests swap in fakes via
  `app.dependency_overrides` — the same mechanism used for the DB session.
- **Chunking.** Sliding word-window with overlap, tracking char offsets per page. Token
  budgets are approximated as words (~0.75 words/token); defaults are 256/40 tokens so a
  chunk stays within `all-MiniLM-L6-v2`'s 256-token sequence limit rather than being
  silently truncated.
- **Vector metadata & scoping.** Each vector carries `owner_id`, `document_id`,
  `chunk_id`, `ordinal`, and (for PDFs) `page`. Every query filters on `owner_id`, so
  retrieval is authz-scoped in the store itself, not just in Postgres.
- **Deletion order.** Delete removes vectors *before* the Postgres row, so a failure can
  never leave orphaned embeddings that outlive their document.
- **Citations.** The grounded prompt numbers each source; the model cites with `[n]`
  markers, and the service maps the markers that actually appear in the answer back to the
  exact source chunks (document, page, snippet). Only genuinely-referenced sources are
  returned and persisted with the assistant message.
