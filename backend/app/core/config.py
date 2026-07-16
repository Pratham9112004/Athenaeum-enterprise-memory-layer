"""Application configuration.

All secrets and environment-specific values come from environment variables (or a
local .env). pydantic-settings validates and types them at startup, so a misconfigured
deployment fails fast and loudly instead of at first use.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "Athenaeum"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_v1_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+psycopg2://athenaeum:athenaeum@localhost:5432/athenaeum",
        alias="DATABASE_URL",
    )

    # ── Vector store (ChromaDB server) ───────────────────────────────────────
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8000, alias="CHROMA_PORT")
    chroma_collection: str = "athenaeum_chunks"

    # ── Auth / JWT ───────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    refresh_cookie_name: str = "athenaeum_refresh"
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")

    # ── AI providers ─────────────────────────────────────────────────────────
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384  # all-MiniLM-L6-v2 output dimensionality

    # ── Vector store tuning ──────────────────────────────────────────────────
    # Cosine distance keeps scores comparable regardless of embedding magnitude.
    chroma_distance: str = "cosine"
    retrieval_top_k: int = 5

    # ── Chat / RAG ───────────────────────────────────────────────────────────
    chat_history_limit: int = 10  # prior turns fed back into the prompt
    chat_max_tokens: int = 800

    # ── Ingestion ────────────────────────────────────────────────────────────
    storage_dir: str = Field(default="storage", alias="STORAGE_DIR")
    max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB
    # Chunk sizing is expressed in tokens but the hand-rolled chunker approximates
    # tokens as whitespace words (~1 word ≈ 1.3 tokens). 256 tokens matches
    # all-MiniLM-L6-v2's max sequence length, so chunks aren't silently truncated.
    chunk_size_tokens: int = 256
    chunk_overlap_tokens: int = 40

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Stored as a raw comma-separated string. Typing this as list[str] would make
    # pydantic-settings attempt json.loads() on the env value before any validator
    # runs, which blows up on a plain string like "http://localhost:5173".
    cors_origins_raw: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
