"""Tests for the FastAPI app entry point — lifespan, middleware, and /metrics endpoint."""

from unittest.mock import patch

import pytest
from app.chaos import get_chaos_state, reset_chaos_state
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_chaos() -> None:
    """Reset chaos state before every test so injection doesn't bleed between tests."""
    reset_chaos_state()


def test_lifespan_calls_create_tables() -> None:
    """Lifespan calls create_tables on startup."""
    with patch("app.main.create_tables") as mock_create:
        with TestClient(app):
            pass
    mock_create.assert_called_once()


def test_metrics_endpoint_returns_prometheus_text() -> None:
    """GET /metrics returns Prometheus text format containing RED metric names."""
    with patch("app.main.create_tables"):
        with TestClient(app) as client:
            response = client.get("/metrics")
    assert response.status_code == 200
    assert "pulseboard_api_requests_total" in response.text


def test_middleware_increments_request_counter() -> None:
    """Metrics middleware records requests so the counter appears in /metrics output."""
    with patch("app.main.create_tables"):
        with TestClient(app) as client:
            client.get("/metrics")
            response = client.get("/metrics")
    assert "pulseboard_api_request_duration_seconds" in response.text


def test_middleware_injects_error_when_chaos_active() -> None:
    """Middleware returns 500 and skips the real handler when error_rate is 1.0."""
    get_chaos_state().error_rate = 1.0
    with patch("app.main.create_tables"):
        with TestClient(app) as client:
            response = client.get("/health")
    assert response.status_code == 500
    assert response.json() == {"detail": "chaos: injected error"}


def test_middleware_skips_chaos_for_chaos_paths() -> None:
    """Chaos injection is not applied to /chaos/* endpoints themselves."""
    get_chaos_state().error_rate = 1.0
    with patch("app.main.create_tables"):
        with TestClient(app) as client:
            response = client.get("/chaos/status")
    assert response.status_code == 200
