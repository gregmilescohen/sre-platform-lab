"""Tests for the pulseboard-worker event publisher."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from app.worker import EVENT_TYPES, build_event, publish_batch


def test_build_event_returns_required_fields() -> None:
    """build_event includes event_name and required metadata fields."""
    event = build_event("page_view")
    assert event["event_name"] == "page_view"
    assert "metadata" in event
    assert "session_id" in event["metadata"]
    assert "emitted_at" in event["metadata"]


@pytest.mark.parametrize("event_type", EVENT_TYPES)
def test_build_event_all_known_types(event_type: str) -> None:
    """build_event works for every event type in EVENT_TYPES."""
    event = build_event(event_type)
    assert event["event_name"] == event_type


def test_build_event_body_is_valid_emit_request() -> None:
    """build_event produces a dict matching the EmitRequest schema (event_name + metadata)."""
    event = build_event("checkout")
    assert set(event.keys()) == {"event_name", "metadata"}
    assert isinstance(event["metadata"], dict)


def test_publish_batch_posts_once_per_event() -> None:
    """publish_batch calls urlopen exactly batch_size times."""
    with patch("app.worker.urllib.request.urlopen") as mock_open:
        ok, err = publish_batch("http://api:8080", batch_size=3)

    assert mock_open.call_count == 3
    assert ok == 3
    assert err == 0


def test_publish_batch_sends_json_to_correct_url() -> None:
    """publish_batch POSTs valid JSON to /events/ on the given base URL."""
    with patch("app.worker.urllib.request.urlopen") as mock_open:
        publish_batch("http://api:8080", batch_size=1)

    req = mock_open.call_args[0][0]
    assert req.full_url == "http://api:8080/events/"
    assert req.get_header("Content-type") == "application/json"
    payload = json.loads(req.data.decode())
    assert "event_name" in payload
    assert "metadata" in payload


def test_publish_batch_counts_errors() -> None:
    """publish_batch returns error count when urlopen raises URLError."""
    with patch(
        "app.worker.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        ok, err = publish_batch("http://api:8080", batch_size=3)

    assert ok == 0
    assert err == 3


def test_publish_batch_partial_failure() -> None:
    """publish_batch correctly tallies mixed success and failure."""
    responses = [MagicMock(), urllib.error.URLError("timeout"), MagicMock()]

    def _side_effect(*_args: object, **_kwargs: object) -> MagicMock:
        val = responses.pop(0)
        if isinstance(val, Exception):
            raise val
        return val  # type: ignore[return-value]

    with patch("app.worker.urllib.request.urlopen", side_effect=_side_effect):
        ok, err = publish_batch("http://api:8080", batch_size=3)

    assert ok == 2
    assert err == 1


class _BreakLoop(Exception):
    """Sentinel to escape the run() infinite loop in tests."""


def test_run_calls_publish_batch_and_sleeps() -> None:
    """run() calls publish_batch and sleeps each iteration."""
    with patch("app.worker.publish_batch", return_value=(5, 0)) as mock_publish:
        with patch("app.worker.time.sleep", side_effect=_BreakLoop):
            with pytest.raises(_BreakLoop):
                from app.worker import run

                run()

    mock_publish.assert_called_once()


def test_run_reads_env_vars() -> None:
    """run() picks up PUBLISH_INTERVAL_SECONDS, BATCH_SIZE, and PULSEBOARD_API_URL."""
    import os

    sleep_args: list[float] = []

    def capture_sleep(interval: float) -> None:
        sleep_args.append(interval)
        raise _BreakLoop

    env = {
        **os.environ,
        "PUBLISH_INTERVAL_SECONDS": "0.5",
        "BATCH_SIZE": "2",
        "PULSEBOARD_API_URL": "http://custom-api:9000",
    }
    with patch.dict(os.environ, env, clear=True):
        with patch("app.worker.publish_batch", return_value=(2, 0)) as mock_publish:
            with patch("app.worker.time.sleep", side_effect=capture_sleep):
                with pytest.raises(_BreakLoop):
                    from app.worker import run

                    run()

    assert sleep_args == [0.5]
    call_kwargs = mock_publish.call_args
    assert call_kwargs[1].get("batch_size") == 2
    assert call_kwargs[0][0] == "http://custom-api:9000"
