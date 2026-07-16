"""Metadata aggregation point for Alembic.

Alembic's ``--autogenerate`` only sees tables whose models have been imported into the
metadata. If a model file is never imported here, autogenerate silently produces an
EMPTY migration — no error, no warning. So EVERY model module must be imported below,
and ``alembic/env.py`` imports this module (and only this module) to pull them all in.

    When you add a new model:  add one import line here.  That's the whole contract.
"""

from app.db.session import Base  # noqa: F401  (re-exported for Alembic target_metadata)

# ── Import every model so its table registers on Base.metadata ────────────────
from app.models.chat import ChatMessage, ChatSession  # noqa: F401
from app.models.document import Document, DocumentChunk  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Document",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
]
