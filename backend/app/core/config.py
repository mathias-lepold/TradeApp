"""
Core: Config
Zentrale Konfiguration via Pydantic Settings — liest aus Umgebungsvariablen / .env.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "TradeApp"
    app_version: str = "2.0.0"
    debug: bool = False

    # Datenbank
    database_url: str = "postgresql+asyncpg://tradeapp:secret@localhost:5432/tradeapp"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 30

    # IBKR
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497
    ibkr_client_id: int = 1

    # Anthropic
    anthropic_api_key: str = ""

    # Security
    secret_key: str = "dev-secret-key-change-in-prod"

    # Portfolio (Prod: aus DB)
    portfolio_value_chf: float = 284620.0
    cash_chf: float = 113080.0
    usd_chf_rate: float = 0.889

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton — wird einmal geladen und gecached."""
    return Settings()
