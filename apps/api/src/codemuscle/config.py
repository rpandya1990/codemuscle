from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CodeMuscle API"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    web_origin: AnyHttpUrl = AnyHttpUrl("http://localhost:3000")
    database_url: str = "postgresql+psycopg://codemuscle:codemuscle@localhost:5432/codemuscle"
    workspace_path: Path | None = None
    ai_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
