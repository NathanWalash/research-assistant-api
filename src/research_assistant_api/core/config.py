from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Research Assistant API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_prefix: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RESEARCH_API_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
