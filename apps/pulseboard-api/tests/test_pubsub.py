"""Tests for Pub/Sub publisher helpers."""

from unittest.mock import MagicMock, patch

from app.pubsub import get_publisher


def test_get_publisher_creates_publisher_client() -> None:
    """get_publisher instantiates a PublisherClient on first call."""
    get_publisher.cache_clear()
    with patch("app.pubsub.pubsub_v1.PublisherClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        result = get_publisher()
    mock_cls.assert_called_once()
    assert result is not None
    get_publisher.cache_clear()


def test_get_publisher_returns_same_instance_on_repeated_calls() -> None:
    """get_publisher returns the cached instance on subsequent calls (singleton)."""
    get_publisher.cache_clear()
    with patch("app.pubsub.pubsub_v1.PublisherClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        first = get_publisher()
        second = get_publisher()
    assert first is second
    assert mock_cls.call_count == 1
    get_publisher.cache_clear()
