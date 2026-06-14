"""
CA Vault Bot - Application Settings
Centralized configuration using pydantic-settings for type safety and validation.
"""
from __future__ import annotations

import os
from typing import List, Optional
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Telegram ──────────────────────────────────────────────────────────────
    bot_token: str
    admin_ids: List[int] = []

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://cavault:password@localhost:5432/cavault_db"
    database_pool_size: int = 20
    database_max_overflow: int = 40
    database_echo: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300
    redis_hot_cache_ttl: int = 60

    # ── Google Drive ──────────────────────────────────────────────────────────
    google_service_account_json: str = "./service_account.json"
    google_service_account_json_content: Optional[str] = None

    # ── Indexer ───────────────────────────────────────────────────────────────
    index_scan_interval_minutes: int = 10
    index_batch_size: int = 100
    max_concurrent_scans: int = 5

    # ── Search ────────────────────────────────────────────────────────────────
    search_results_per_page: int = 5
    search_fuzzy_threshold: int = 65
    search_max_results: int = 200
    search_cache_ttl: int = 120

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_searches_per_minute: int = 20
    rate_limit_downloads_per_hour: int = 50
    rate_limit_window_seconds: int = 60

    # ── File Size ─────────────────────────────────────────────────────────────
    telegram_max_file_size: int = 52_428_800  # 50 MB

    # ── Environment ───────────────────────────────────────────────────────────
    environment: str = "production"
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()


settings = get_settings()
