"""Setup verification.

Run after generating/altering each feature, before manual API/GUI testing. Catches the
"silently broken" class of bugs: a module that won't import, a missing router, or a
model that exists but was never imported into Alembic's metadata (which would make
autogenerate emit an empty migration).

    python scripts/verify_setup.py
"""

import importlib
import os
import sys

# Make the backend root importable regardless of how this script is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 1. Every module must import cleanly ──────────────────────────────────────
MODULES = [
    "app.main",
    "app.core.config",
    "app.core.security",
    "app.core.logging",
    "app.core.exceptions",
    "app.db.base",
    "app.db.session",
    "app.models.user",
    "app.models.document",
    "app.models.chat",
    "app.schemas.user",
    "app.schemas.auth",
    "app.schemas.document",
    "app.schemas.search",
    "app.schemas.chat",
    "app.repositories.base",
    "app.repositories.user_repository",
    "app.repositories.document_repository",
    "app.repositories.chat_repository",
    "app.services.auth_service",
    "app.services.storage",
    "app.services.embeddings",
    "app.services.vector_store",
    "app.services.parsing",
    "app.services.chunking",
    "app.services.pipeline",
    "app.services.retrieval",
    "app.services.document_service",
    "app.services.search_service",
    "app.services.llm",
    "app.services.chat_service",
    "app.api.deps",
    "app.api.v1.router",
    "app.api.v1.endpoints.auth",
    "app.api.v1.endpoints.health",
    "app.api.v1.endpoints.documents",
    "app.api.v1.endpoints.search",
    "app.api.v1.endpoints.chat",
]

# ── 2. Named objects that must exist (module attr -> label) ──────────────────
EXPECTED_ATTRS = {
    "app.main": ["app", "create_app"],
    "app.core.security": [
        "hash_password",
        "verify_password",
        "create_access_token",
        "create_refresh_token",
        "decode_token",
    ],
    "app.services.auth_service": ["AuthService"],
    "app.services.document_service": ["DocumentService", "ALLOWED_TYPES"],
    "app.services.pipeline": ["ingest_document", "run_ingestion"],
    "app.services.chunking": ["chunk_pages"],
    "app.services.parsing": ["parse_document"],
    "app.services.retrieval": ["retrieve"],
    "app.services.search_service": ["SearchService"],
    "app.services.chat_service": ["ChatService", "build_sources_block", "map_citations"],
    "app.services.embeddings": ["get_embedder", "SentenceTransformerEmbedder"],
    "app.services.vector_store": ["get_vector_store", "ChromaVectorStore"],
    "app.services.llm": ["get_llm", "GeminiProvider"],
    "app.repositories.user_repository": ["UserRepository"],
    "app.repositories.document_repository": ["DocumentRepository"],
    "app.repositories.chat_repository": ["ChatRepository"],
    "app.models.user": ["User"],
    "app.models.document": ["Document", "DocumentChunk", "DocumentStatus"],
    "app.models.chat": ["ChatSession", "ChatMessage"],
    "app.api.v1.router": ["api_router"],
}

# ── 3. Routes that must be registered on the app ─────────────────────────────
EXPECTED_ROUTES = [
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/auth/me"),
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/documents"),
    ("POST", "/api/v1/documents"),
    ("GET", "/api/v1/documents/{document_id}"),
    ("DELETE", "/api/v1/documents/{document_id}"),
    ("POST", "/api/v1/search"),
    ("POST", "/api/v1/chat"),
    ("GET", "/api/v1/chat/sessions"),
    ("GET", "/api/v1/chat/sessions/{session_id}"),
]


def _fail(msg: str) -> None:
    print(f"  \u2717 {msg}")


def _ok(msg: str) -> None:
    print(f"  \u2713 {msg}")


def check_imports() -> list[str]:
    errors: list[str] = []
    print("Imports:")
    for name in MODULES:
        try:
            importlib.import_module(name)
            _ok(name)
        except Exception as exc:  # noqa: BLE001 - report, don't crash
            _fail(f"{name}: {exc}")
            errors.append(f"import {name}: {exc}")
    return errors


def check_attrs() -> list[str]:
    errors: list[str] = []
    print("Expected objects:")
    for mod_name, attrs in EXPECTED_ATTRS.items():
        mod = importlib.import_module(mod_name)
        for attr in attrs:
            if hasattr(mod, attr):
                _ok(f"{mod_name}.{attr}")
            else:
                _fail(f"{mod_name}.{attr} missing")
                errors.append(f"{mod_name}.{attr} missing")
    return errors


def check_routes() -> list[str]:
    errors: list[str] = []
    print("Routes:")
    from app.main import app

    registered = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set()) or set()
    }
    for method, path in EXPECTED_ROUTES:
        if (method, path) in registered:
            _ok(f"{method} {path}")
        else:
            _fail(f"{method} {path} not registered")
            errors.append(f"route {method} {path} missing")
    return errors


def check_models_registered_for_alembic() -> list[str]:
    """Every mapped model's table must be on the metadata Alembic targets.

    Alembic imports ``app.db.base`` for ``target_metadata``. If a model file exists but
    its import line is missing from ``app.db.base``, its table won't be on that metadata
    and autogenerate will silently miss it. We detect that mismatch here.
    """
    errors: list[str] = []
    print("Alembic model registration:")

    from app.db.base import Base

    metadata_tables = set(Base.metadata.tables.keys())

    # Discover every declarative model actually defined under app.models.*
    import pkgutil

    import app.models as models_pkg

    discovered: dict[str, str] = {}  # tablename -> module
    for mod in pkgutil.iter_modules(models_pkg.__path__):
        module = importlib.import_module(f"app.models.{mod.name}")
        for obj in vars(module).values():
            table = getattr(obj, "__tablename__", None)
            if isinstance(table, str):
                discovered[table] = f"app.models.{mod.name}"

    for table, module in discovered.items():
        if table in metadata_tables:
            _ok(f"'{table}' ({module}) registered on Base.metadata")
        else:
            _fail(
                f"'{table}' defined in {module} but NOT imported in app/db/base.py "
                f"-- add its import there or autogenerate will skip it"
            )
            errors.append(f"model '{table}' not registered in app/db/base.py")
    return errors


def main() -> int:
    print("=" * 70)
    print("Athenaeum setup verification")
    print("=" * 70)

    errors: list[str] = []
    errors += check_imports()
    errors += check_attrs()
    errors += check_routes()
    errors += check_models_registered_for_alembic()

    print("=" * 70)
    if errors:
        print(f"FAILED with {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
