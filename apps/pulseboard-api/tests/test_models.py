"""Tests for app/models.py re-export."""

from datetime import datetime


def test_utcnow_returns_utc_aware_datetime() -> None:
    """_utcnow (re-exported) returns a timezone-aware datetime in UTC."""
    from app.models import _utcnow

    result = _utcnow()
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_new_ulid_returns_26_char_string() -> None:
    """_new_ulid (re-exported) returns a 26-character ULID string."""
    from app.models import _new_ulid

    result = _new_ulid()
    assert isinstance(result, str)
    assert len(result) == 26


def test_new_ulid_is_unique_per_call() -> None:
    """_new_ulid generates a different value on each call."""
    from app.models import _new_ulid

    assert _new_ulid() != _new_ulid()
