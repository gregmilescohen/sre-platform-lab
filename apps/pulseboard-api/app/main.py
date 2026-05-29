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
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.db import create_tables
from app.metrics import record_request
from app.routers import events, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """FastAPI lifespan context manager — creates DB tables on startup."""
    create_tables()
    yield


app = FastAPI(
    title="PulseBoard API",
    version="0.1.0",
    description="Backend API for the PulseBoard demo workload in the Reliability Lab.",
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Record RED metrics for every HTTP request."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    record_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration,
    )
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metrics scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health.router)
app.include_router(events.router, prefix="/events", tags=["events"])
