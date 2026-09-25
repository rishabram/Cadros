"""Cadros Platform Delivery API Service."""
from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cadros.platform")

# Optional Sentry observability initialization
if settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            release=f"cadros@{__version__}",
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration()],
        )
        logger.info("Sentry observability initialized successfully.")
    except Exception as exc:
        logger.warning("Failed to initialize Sentry: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Cadros Platform API booting up. Environment: %s", settings.environment)
    yield
    logger.info("Cadros Platform API shutting down.")


app = FastAPI(
    title="Cadros Platform Delivery API",
    version=__version__,
    description="High-fidelity spatial parcel computation and platform runtime engine.",
    lifespan=lifespan,
)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    return {
        "service": "cadros-platform-api",
        "version": __version__,
        "environment": settings.environment,
        "docs": "/docs",
        "status": "operational",
    }


@app.get("/healthz", tags=["Observability"])
async def health_check() -> Dict[str, Any]:
    """Liveness probe for Heroku / load balancer monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
    }


@app.get("/readyz", tags=["Observability"])
async def readiness_check() -> Dict[str, Any]:
    """Readiness probe to confirm core assets are accessible."""
    checks = {}
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Verify rulegraph store accessibility
    rulegraph_store = os.path.join(base_dir, "rulegraph", "verified_rules.json")
    checks["rulegraph_store"] = os.path.isfile(rulegraph_store)

    # Verify caddy drop inputs accessibility
    caddy_uses = os.path.join(base_dir, "caddy_drop", "verified_uses_mu.json")
    checks["caddy_uses"] = os.path.isfile(caddy_uses)

    all_ready = all(checks.values())
    if not all_ready:
        logger.error("Readiness check failed: %s", checks)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/version", tags=["Observability"])
async def version_info() -> Dict[str, Any]:
    """Version and deployment metadata for rollback verification."""
    return {
        "service": "cadros-platform",
        "version": __version__,
        "commit": settings.git_commit,
        "environment": settings.environment,
        "heroku_app": settings.heroku_app_name,
        "release_version": settings.heroku_release_version,
    }
