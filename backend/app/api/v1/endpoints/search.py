"""Semantic search endpoint."""

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, EmbedderDep, VectorStoreDep
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(
    payload: SearchRequest,
    current_user: CurrentUser,
    db: DbSession,
    embedder: EmbedderDep,
    vector_store: VectorStoreDep,
) -> SearchResponse:
    return SearchService(db, embedder=embedder, vector_store=vector_store).search(
        owner_id=current_user.id, query=payload.query, top_k=payload.top_k
    )
