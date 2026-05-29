"""Tests for ORM model default factory functions."""

from datetime import datetime

from app.models import _new_ulid, _utcnow


def test_utcnow_returns_utc_aware_datetime() -> None:
    """_utcnow returns a timezone-aware datetime in UTC."""
    result = _utcnow()
    assert isinstance(result, datetime)
    assert result.tzinfo is not None
    assert result.utcoffset().total_seconds() == 0  # type: ignore[union-attr]


def test_new_ulid_returns_26_char_string() -> None:
    """_new_ulid returns a 26-character ULID string."""
    result = _new_ulid()
    assert isinstance(result, str)
    assert len(result) == 26


def test_new_ulid_is_unique_per_call() -> None:
    """_new_ulid generates a different value on each call."""
    assert _new_ulid() != _new_ulid()
