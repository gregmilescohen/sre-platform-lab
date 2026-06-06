"""Tests for chaos state and injection helpers."""

import time

import pytest
from app.chaos import ChaosState, apply_chaos_delay, should_inject_error


@pytest.fixture()
def clean_state() -> ChaosState:
    """Return a fresh ChaosState with all modes off."""
    return ChaosState()


def test_chaos_state_defaults_are_off(clean_state: ChaosState) -> None:
    """Default ChaosState has all modes disabled."""
    assert clean_state.slow_ms == 0
    assert clean_state.error_rate == 0.0
    assert not clean_state.leak_active


def test_apply_chaos_delay_noop_when_zero(clean_state: ChaosState) -> None:
    """apply_chaos_delay adds no measurable delay when slow_ms is 0."""
    start = time.perf_counter()
    apply_chaos_delay(clean_state)
    assert time.perf_counter() - start < 0.05


def test_should_inject_error_never_when_rate_zero(clean_state: ChaosState) -> None:
    """No errors injected when error_rate is 0."""
    assert not any(should_inject_error(clean_state) for _ in range(100))


def test_should_inject_error_always_when_rate_one(clean_state: ChaosState) -> None:
    """Every request errors when error_rate is 1.0."""
    clean_state.error_rate = 1.0
    assert all(should_inject_error(clean_state) for _ in range(10))


def test_should_inject_error_probabilistic(clean_state: ChaosState) -> None:
    """50% error rate produces roughly 50% errors across 1000 samples."""
    clean_state.error_rate = 0.5
    results = [should_inject_error(clean_state) for _ in range(1000)]
    ratio = sum(results) / len(results)
    assert 0.4 < ratio < 0.6
