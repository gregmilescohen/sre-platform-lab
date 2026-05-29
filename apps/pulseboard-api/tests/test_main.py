"""Tests for the FastAPI app entry point — lifespan, middleware, and /metrics endpoint."""

from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient


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
