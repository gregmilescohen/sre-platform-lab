"""Tests for app/models.py."""


def test_utcnow_returns_datetime() -> None:
    """_utcnow returns a datetime instance."""
    from datetime import datetime

    from app.models import _utcnow

    result = _utcnow()
    assert isinstance(result, datetime)


def test_new_ulid_returns_string() -> None:
    """_new_ulid returns a 26-character ULID string."""
    from app.models import _new_ulid

    result = _new_ulid()
    assert isinstance(result, str)
    assert len(result) == 26
