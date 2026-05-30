"""Tests for app/db.py."""


def test_get_db_returns_session() -> None:
    """get_db returns a usable SQLAlchemy session."""
    from app.db import get_db

    db = get_db()
    assert db is not None
    db.close()


def test_create_tables_calls_metadata_create_all() -> None:
    """create_tables delegates to Base.metadata.create_all."""
    from unittest.mock import patch

    from app.db import create_tables

    with patch("app.db.Base.metadata.create_all") as mock_create:
        create_tables()
    mock_create.assert_called_once()


def test_postgresql_url_rewrite() -> None:
    """DATABASE_URL with postgresql:// gets psycopg2 dialect prefix injected."""
    import importlib
    import sys
    from unittest.mock import patch

    sys.modules.pop("app.db", None)
    with patch.dict("os.environ", {"DATABASE_URL": "postgresql://u:p@host/db"}):
        import app.db

        importlib.reload(app.db)
        assert "psycopg2" in app.db.DATABASE_URL
    sys.modules.pop("app.db", None)
    import app.db  # re-import so reload has a module reference

    importlib.reload(app.db)
