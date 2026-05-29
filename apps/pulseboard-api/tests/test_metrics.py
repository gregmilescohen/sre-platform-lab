"""Tests for Prometheus RED metrics helpers."""

from app.metrics import record_request


def test_record_request_does_not_raise() -> None:
    """record_request accepts valid inputs without raising."""
    record_request(method="GET", endpoint="/health", status_code=200, duration=0.01)


def test_record_request_records_error_status() -> None:
    """record_request accepts 5xx status codes without raising."""
    record_request(method="POST", endpoint="/events", status_code=500, duration=0.25)


def test_record_request_records_zero_duration() -> None:
    """record_request handles zero duration without raising."""
    record_request(method="GET", endpoint="/metrics", status_code=200, duration=0.0)
