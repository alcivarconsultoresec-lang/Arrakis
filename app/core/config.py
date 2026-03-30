"""Pydantic Settings para configuración de la aplicación."""
from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global de la aplicación."""

    # App
    APP_NAME: str = "Ω JARBIS Enterprise"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./jarbis.db")
    DB_ECHO: bool = False

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production-min-32-chars!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas

    # Multi-tenant
    DEFAULT_CHAIN_ID: str = "default-chain"

    # AI/ML (opcional)
    AI_ENABLED: bool = False
    AI_PROVIDER: str | None = None
    AI_API_KEY: str | None = None

    # Notifications
    FIREBASE_CREDENTIALS: str | None = None

    # POS Integration
    POS_PROVIDER: str | None = None  # toast, square, clover
    POS_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Obtiene configuración cached."""
    return Settings()
