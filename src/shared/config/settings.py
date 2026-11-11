from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "Strategic Indicators AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    DEFAULT_CURRENCY: str = "USD"

    # AI Provider configuration: "ollama", "google", "openai", "fake"
    AI_PROVIDER: Literal["ollama", "google", "openai", "fake"] = "ollama"
    AI_MODEL: str = "llama3.2"
    AI_BASE_URL: str = "http://localhost:11434/v1"
    AI_API_KEY: str | None = None
    AI_TIMEOUT_SECONDS: float = 30.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
