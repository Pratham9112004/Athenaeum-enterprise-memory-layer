"""Document request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: str
    extension: str
    size_bytes: int
    status: str
    error: str | None
    chunk_count: int
    created_at: datetime
