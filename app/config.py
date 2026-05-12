from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gov RAG"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8080
    database_url: str = "sqlite:///./gov_rag.db"
    llm_provider: str = "stub"
    llm_model: str = ""
    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
SOURCES_DIR = BASE_DIR / "sources"
