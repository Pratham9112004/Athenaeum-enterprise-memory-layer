"""File storage.

An interface plus a local-disk implementation. Keeping this behind a Protocol means
Feature-later S3/MinIO storage is a drop-in replacement: the document service only ever
sees ``save`` / ``read`` / ``delete``.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol

from app.core.config import settings


class FileStorage(Protocol):
    def save(self, owner_id: int, filename: str, data: bytes) -> str: ...
    def read(self, storage_path: str) -> bytes: ...
    def delete(self, storage_path: str) -> None: ...


class LocalFileStorage:
    """Stores files under ``<base_dir>/<owner_id>/<uuid><ext>``.

    The stored name is randomized to avoid collisions and path-traversal via the
    original filename; the human-readable name lives in Postgres, not on disk.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.storage_dir)

    def save(self, owner_id: int, filename: str, data: bytes) -> str:
        ext = Path(filename).suffix.lower()
        owner_dir = self.base_dir / str(owner_id)
        owner_dir.mkdir(parents=True, exist_ok=True)
        target = owner_dir / f"{uuid.uuid4().hex}{ext}"
        target.write_bytes(data)
        return str(target)

    def read(self, storage_path: str) -> bytes:
        return Path(storage_path).read_bytes()

    def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            path.unlink()


def get_storage() -> FileStorage:
    return LocalFileStorage()
