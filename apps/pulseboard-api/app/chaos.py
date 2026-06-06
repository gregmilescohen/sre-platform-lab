"""Chaos state and injection helpers for pulseboard-api.

A module-level ChaosState singleton tracks active failure modes.
The chaos router (routers/chaos.py) exposes HTTP endpoints to toggle modes.
The metrics middleware in main.py applies them to every non-chaos request.
"""

import random
import time
from dataclasses import dataclass, field


@dataclass
class ChaosState:
    """Holds the current chaos injection configuration."""

    slow_ms: int = field(default=0)
    error_rate: float = field(default=0.0)
    leak_active: bool = field(default=False)


_state = ChaosState()


def get_chaos_state() -> ChaosState:
    """Return the module-level ChaosState singleton."""
    return _state


def reset_chaos_state() -> None:
    """Reset all chaos modes to their off defaults."""
    global _state
    _state = ChaosState()


def apply_chaos_delay(state: ChaosState) -> None:
    """Sleep for state.slow_ms milliseconds if slow mode is active."""
    if state.slow_ms > 0:
        time.sleep(state.slow_ms / 1000.0)


def should_inject_error(state: ChaosState) -> bool:
    """Return True with probability state.error_rate."""
    if state.error_rate <= 0.0:
        return False
    return random.random() < state.error_rate
