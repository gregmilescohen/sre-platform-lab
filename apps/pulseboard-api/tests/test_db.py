"""Tests for database engine, session factory, and ORM utilities."""

import importlib
from unittest.mock import MagicMock, patch

import pytest


def test_create_tables_calls_metadata_create_all() -> None:
    """create_tables delegates to Base.metadata.create_all."""
    from app.db import create_tables

    with patch("app.db.Base") as mock_base:
        create_tables()
    mock_base.metadata.create_all.assert_called_once()


def test_get_db_yields_a_session() -> None:
    """get_db yields a SQLAlchemy session."""
    from app.db import get_db

    with patch("app.db.SessionLocal") as mock_local:
        mock_session = MagicMock()
        mock_local.return_value = mock_session
        gen = get_db()
        session = next(gen)
    assert session is mock_session


def test_get_db_closes_session_on_exit() -> None:
    """get_db closes the session in the finally block after the request completes."""
    from app.db import get_db

    with patch("app.db.SessionLocal") as mock_local:
        mock_session = MagicMock()
        mock_local.return_value = mock_session
        gen = get_db()
        next(gen)
        try:
            next(gen)
        except StopIteration:
            pass
    mock_session.close.assert_called_once()


def test_postgresql_url_rewritten_to_psycopg2(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL with postgresql:// prefix is rewritten to postgresql+psycopg2://."""
    import app.db as db_module

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/test")
    importlib.reload(db_module)
    assert db_module.DATABASE_URL.startswith("postgresql+psycopg2://")

    # Restore sqlite default so subsequent tests are unaffected
    monkeypatch.delenv("DATABASE_URL")
    importlib.reload(db_module)
