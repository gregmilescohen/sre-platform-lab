"""Unit tests for the /health endpoint.

Uses unittest.mock to mock the SQLAlchemy Session — no real DB required.
"""

from unittest.mock import MagicMock

from app.routers.health import health
from sqlalchemy.exc import OperationalError


def test_health_returns_ok_when_db_reachable() -> None:
    """Health returns ok status when DB is reachable."""
    mock_db = MagicMock()
    result = health(db=mock_db)
    assert result["status"] == "ok"
    assert result["db"] == "ok"


def test_health_calls_db_execute() -> None:
    """Health calls db.execute to probe the database."""
    mock_db = MagicMock()
    health(db=mock_db)
    mock_db.execute.assert_called_once()


def test_health_returns_degraded_when_db_raises() -> None:
    """Health returns degraded status when DB raises OperationalError."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = OperationalError("connection refused", {}, Exception())
    result = health(db=mock_db)
    assert result["status"] == "degraded"
    assert result["db"] == "error"


def test_health_db_error_does_not_raise() -> None:
    """Health endpoint must not propagate DB exceptions — it should degrade gracefully."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("unexpected error")
    result = health(db=mock_db)
    assert result["status"] == "degraded"
