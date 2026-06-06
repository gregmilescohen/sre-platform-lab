"""Tests for the chaos injection router endpoints."""

import pytest
from app.chaos import get_chaos_state, reset_chaos_state
from app.routers.chaos import (
    ErrorRequest,
    SlowRequest,
    reset,
    set_errors,
    set_leak,
    set_slow,
    status,
)


@pytest.fixture(autouse=True)
def _reset_chaos() -> None:
    """Reset the module-level singleton before every test."""
    reset_chaos_state()


def test_set_slow_updates_state() -> None:
    """POST /chaos/slow sets slow_ms on the singleton."""
    result = set_slow(SlowRequest(delay_ms=500))
    assert result == {"chaos": "slow", "delay_ms": 500}
    assert get_chaos_state().slow_ms == 500


def test_set_errors_updates_state() -> None:
    """POST /chaos/errors sets error_rate on the singleton."""
    result = set_errors(ErrorRequest(rate=0.75))
    assert result == {"chaos": "errors", "error_rate": 0.75}
    assert get_chaos_state().error_rate == 0.75


def test_set_leak_updates_state() -> None:
    """POST /chaos/leak sets leak_active on the singleton."""
    result = set_leak(active=True)
    assert result == {"chaos": "leak", "active": True}
    assert get_chaos_state().leak_active is True


def test_reset_clears_all_modes() -> None:
    """POST /chaos/reset restores all modes to defaults."""
    state = get_chaos_state()
    state.slow_ms = 2000
    state.error_rate = 0.5
    state.leak_active = True
    result = reset()
    assert result == {"chaos": "reset", "state": "clean"}
    fresh = get_chaos_state()
    assert fresh.slow_ms == 0
    assert fresh.error_rate == 0.0
    assert not fresh.leak_active


def test_status_returns_current_state() -> None:
    """GET /chaos/status reflects the current singleton values."""
    state = get_chaos_state()
    state.slow_ms = 300
    state.error_rate = 0.1
    result = status()
    assert result == {"slow_ms": 300, "error_rate": 0.1, "leak_active": False}
