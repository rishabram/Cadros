"""Tests for Cadros Platform Delivery API, runtime health checks, and lifecycle."""
import asyncio
from unittest.mock import patch
import pytest
from starlette.testclient import TestClient

from app import __version__
from app.config import settings
from app.main import app, lifespan

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "cadros-platform-api"
    assert data["version"] == __version__
    assert data["status"] == "operational"


def test_healthz_liveness():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "python_version" in data


def test_readyz_readiness_healthy():
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["rulegraph_store"] is True
    assert data["checks"]["caddy_uses"] is True


def test_readyz_readiness_failure():
    with patch("os.path.isfile", return_value=False):
        response = client.get("/readyz")
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["checks"]["rulegraph_store"] is False


def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "cadros-platform"
    assert data["version"] == __version__
    assert "commit" in data
    assert "environment" in data


def test_settings_defaults():
    assert settings.port == 8000
    assert settings.environment == "development"
    assert settings.log_level.lower() == "info"


def test_lifespan_context():
    async def run():
        async with lifespan(app):
            pass
    asyncio.run(run())
