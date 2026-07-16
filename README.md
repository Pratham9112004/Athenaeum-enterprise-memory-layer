# Athenaeum

**Enterprise Memory Layer** — store an organization's internal knowledge (docs,
transcripts, SOPs, design notes) and query it in natural language, getting answers with
citations back to the exact source.

> _An athenaeum is an institution devoted to the collection and retrieval of knowledge._

---

## Status

This repository is being built feature-by-feature through the MVP. What's live now:

| # | Feature | Backend | GUI | Status |
|---|---------|---------|-----|--------|
| 1 | **Auth** — register, login, JWT, protected routes | ✅ | ✅ | **Done, verified** |
| 2 | **Document upload** (PDF/DOCX/TXT/MD), list, delete | ✅ | ✅ | **Done, verified** |
| 3 | **Parse → chunk → embed → ChromaDB pipeline** | ✅ | ✅ | **Done, verified** |
| 4 | **Semantic search** | ✅ | ✅ | **Done, verified** |
| 5 | **Chat with documents (RAG) + citations** | ✅ | ✅ | **Done, verified** |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system design.

---

## Quickstart (Docker)

```bash
cp .env.example .env
# Edit .env: set a strong JWT_SECRET_KEY.
# Set OPENAI_API_KEY to enable chat (Feature 5). Upload, processing, and search
# all work without it — chat returns a clear 503 until a key is present.
docker compose up --build
```

Then open:

- **App:** http://localhost:5173
- **API docs (Swagger):** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

The backend container runs `alembic upgrade head` on start, so the schema is created
automatically. Compose also brings up **ChromaDB** (the vector store) and a **`storage`
volume** for uploaded files — no extra setup needed.

**Try the full flow:** register → **Documents** (upload a PDF/DOCX/TXT/MD and watch it
reach `ready`) → **Search** (semantic query over your files) → **Chat** (ask a question
and get an answer with clickable citations back to the source).

> First build is slow: the backend image installs the AI stack (sentence-transformers
> pulls PyTorch). Subsequent builds are cached.

---

## Local development (without Docker)

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg2://athenaeum:athenaeum@localhost:5432/athenaeum"
export JWT_SECRET_KEY="dev-secret"

alembic upgrade head
python scripts/verify_setup.py      # sanity-check wiring before running
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
echo 'VITE_API_URL=http://localhost:8000/api/v1' > .env
npm run dev
```

---

## Testing & verification

```bash
cd backend
python scripts/verify_setup.py      # imports every module, checks routes + Alembic models
pytest -q                           # auth + security suite (in-memory SQLite, no DB needed)
ruff check app scripts tests
black --check app scripts tests

cd ../frontend
npm run typecheck
npm run build
```

`scripts/verify_setup.py` is the first line of defense: it catches unimportable modules,
missing routers, and — critically — any model that exists but was never imported into
Alembic's metadata (which would otherwise cause silent empty migrations).

---

## Project structure

```
athenaeum/
├── docker-compose.yml          # postgres + chromadb + backend + frontend
├── .env.example
├── docs/ARCHITECTURE.md
├── backend/                    # FastAPI, Clean Architecture (api → service → repo → db)
│   ├── app/
│   │   ├── main.py
│   │   ├── core/               # config, security (bcrypt+JWT), logging, exceptions
│   │   ├── db/                 # session + base (imports all models for Alembic)
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── repositories/       # data access
│   │   ├── services/           # business logic (unit-tested)
│   │   └── api/v1/endpoints/   # routers
│   ├── alembic/                # migrations
│   ├── scripts/verify_setup.py
│   ├── tests/
│   └── requirements.txt
└── frontend/                   # React + Vite + TypeScript + Tailwind
    └── src/
        ├── lib/                # api client (in-memory token + silent refresh)
        ├── context/            # AuthContext
        ├── components/         # ui kit, layout, route guard
        └── pages/              # Login, Register, Overview, Documents, Search, Chat
```

---

## Security notes

- **Passwords:** hashed with `bcrypt` called directly (not passlib), input truncated to
  bcrypt's 72-byte limit.
- **Tokens:** short-lived **access token in browser memory only** (never localStorage,
  so XSS can't read it); long-lived **refresh token in an httpOnly, SameSite=Lax,
  path-scoped cookie** the JS never sees. The SPA silently refreshes on load and on 401.
  Set `COOKIE_SECURE=true` when serving over HTTPS.
- **Secrets:** all via environment variables; nothing hardcoded.

---

## Tech stack

FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · ChromaDB · sentence-transformers
(`all-MiniLM-L6-v2`) · OpenAI · PyMuPDF / python-docx · React · Vite · TypeScript ·
Tailwind · Docker Compose · Pytest · Ruff + Black.
