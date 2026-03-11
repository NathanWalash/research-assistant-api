from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET_KEY = "change-this-development-secret"
MIN_JWT_SECRET_KEY_LENGTH = 32


def normalize_database_url(database_url: str) -> str:
    parts = urlsplit(database_url)
    if parts.scheme == "postgres":
        return urlunsplit(("postgresql+psycopg", parts.netloc, parts.path, parts.query, parts.fragment))
    if parts.scheme == "postgresql":
        return urlunsplit(("postgresql+psycopg", parts.netloc, parts.path, parts.query, parts.fragment))
    return database_url


class Settings(BaseSettings):
    app_name: str = "Research Assistant API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_prefix: str = ""
    database_url: str = (
        "postgresql+psycopg://research_user:research_password@localhost:5433/"
        "research_assistant"
    )
    jwt_secret_key: str = DEFAULT_JWT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    embedding_dimensions: int = 384
    dataset_csv_path: Path = Path("UniOfLeedsArticles2018_to_Present.csv")
    citation_edges_csv_path: Path | None = None
    ingestion_batch_size: int = 500
    mcp_enabled: bool = False
    mcp_name: str = "Research Assistant MCP"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8001
    mcp_mount_path: str = "/mcp"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RESEARCH_API_",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_constraints(self) -> "Settings":
        self.database_url = normalize_database_url(self.database_url)
        if not self.mcp_mount_path.startswith("/"):
            self.mcp_mount_path = f"/{self.mcp_mount_path}"

        if self.environment != "production":
            return self

        if self.jwt_secret_key == DEFAULT_JWT_SECRET_KEY:
            raise ValueError(
                "RESEARCH_API_JWT_SECRET_KEY must not use the development default in production"
            )
        if len(self.jwt_secret_key) < MIN_JWT_SECRET_KEY_LENGTH:
            raise ValueError(
                f"RESEARCH_API_JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_KEY_LENGTH} characters long in production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
