from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    jwt_secret_key: str = "change-this-development-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    embedding_dimensions: int = 384
    dataset_csv_path: Path = Path("UniOfLeedsArticles2018_to_Present.csv")
    citation_edges_csv_path: Path | None = None
    ingestion_batch_size: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RESEARCH_API_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
