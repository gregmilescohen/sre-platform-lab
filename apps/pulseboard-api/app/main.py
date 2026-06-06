"""PulseBoard API — FastAPI application entry point.

Startup: creates DB tables if they don't exist.
Middleware: records RED metrics (rate, errors, duration) for every request.
Routes:
  GET  /health   Liveness/readiness probe
  GET  /metrics  Prometheus metrics scrape endpoint
  POST /events   Publish an event to the Pub/Sub topic
  GET  /events   Read time-bucketed event counts from event_log
"""

import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.chaos import apply_chaos_delay, get_chaos_state, should_inject_error
from app.db import create_tables
from app.metrics import record_request
from app.routers import chaos as chaos_router
from app.routers import events, health
from app.telemetry import setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan context manager — sets up tracing and creates DB tables on startup."""
    setup_tracing()
    SQLAlchemyInstrumentor().instrument()
    create_tables()
    yield


app = FastAPI(
    title="PulseBoard API",
    version="0.1.0",
    description="Backend API for the PulseBoard demo workload in the Reliability Lab.",
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Record RED metrics and apply chaos injection on every request."""
    start = time.perf_counter()
    path = request.url.path

    if not path.startswith("/chaos") and path != "/metrics":
        state = get_chaos_state()
        apply_chaos_delay(state)
        if should_inject_error(state):
            duration = time.perf_counter() - start
            record_request(request.method, path, 500, duration)
            return Response(
                content='{"detail":"chaos: injected error"}',
                status_code=500,
                media_type="application/json",
            )

    response = await call_next(request)
    duration = time.perf_counter() - start
    record_request(request.method, path, response.status_code, duration)
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metrics scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health.router)
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(chaos_router.router, prefix="/chaos", tags=["chaos"])
