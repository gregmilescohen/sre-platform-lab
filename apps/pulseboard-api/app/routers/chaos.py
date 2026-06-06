"""Chaos injection router for pulseboard-api.

Exposes endpoints to enable/disable failure modes used in the SRE demo:
  POST /chaos/slow    — set artificial request latency
  POST /chaos/errors  — set error injection rate
  POST /chaos/leak    — toggle memory bloat simulation
  POST /chaos/reset   — clear all chaos modes
  GET  /chaos/status  — current chaos configuration
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.chaos import get_chaos_state, reset_chaos_state

router = APIRouter()


class SlowRequest(BaseModel):
    """Request body for enabling slow mode."""

    delay_ms: int = Field(..., ge=0, le=30000)


class ErrorRequest(BaseModel):
    """Request body for enabling error injection."""

    rate: float = Field(..., ge=0.0, le=1.0)


@router.post("/slow")
def set_slow(req: SlowRequest) -> dict:
    """Set artificial latency for every request."""
    get_chaos_state().slow_ms = req.delay_ms
    return {"chaos": "slow", "delay_ms": req.delay_ms}


@router.post("/errors")
def set_errors(req: ErrorRequest) -> dict:
    """Set the fraction of requests that return HTTP 500."""
    get_chaos_state().error_rate = req.rate
    return {"chaos": "errors", "error_rate": req.rate}


@router.post("/leak")
def set_leak(active: bool = True) -> dict:
    """Toggle memory bloat simulation."""
    get_chaos_state().leak_active = active
    return {"chaos": "leak", "active": active}


@router.post("/reset")
def reset() -> dict:
    """Clear all active chaos modes."""
    reset_chaos_state()
    return {"chaos": "reset", "state": "clean"}


@router.get("/status")
def status() -> dict:
    """Return the current chaos configuration."""
    state = get_chaos_state()
    return {
        "slow_ms": state.slow_ms,
        "error_rate": state.error_rate,
        "leak_active": state.leak_active,
    }
