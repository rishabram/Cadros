"""Cadros Platform Configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    sentry_dsn: str | None = os.getenv("SENTRY_DSN")
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    heroku_app_name: str | None = os.getenv("HEROKU_APP_NAME")
    heroku_release_version: str | None = os.getenv("HEROKU_RELEASE_VERSION")
    git_commit: str = os.getenv("HEROKU_SLUG_COMMIT", os.getenv("GIT_COMMIT", "local-dev"))


settings = Settings()
