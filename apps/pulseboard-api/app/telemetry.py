"""OpenTelemetry tracing and logging setup for pulseboard-api.

Only initialises when OTEL_EXPORTER_OTLP_ENDPOINT is set so the service
starts cleanly in environments without a collector (e.g. unit tests).
When active, all log records emitted during a live span include trace_id
and span_id fields so Grafana can correlate traces with Loki logs.
"""

import json
import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_SERVICE = "pulseboard-api"
_ZERO_TRACE_ID = "0" * 32


class _JsonFormatter(logging.Formatter):
    """Emit log records as JSON, injecting OTel trace_id/span_id when present."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the log record serialised as a JSON string."""
        payload: dict[str, object] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": _SERVICE,
        }
        trace_id: str = getattr(record, "otelTraceID", _ZERO_TRACE_ID)
        if trace_id != _ZERO_TRACE_ID:
            payload["trace_id"] = trace_id
            payload["span_id"] = getattr(record, "otelSpanID", "")
        return json.dumps(payload)


def _configure_json_logging() -> None:
    """Replace the root logging handler with the JSON formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # uvicorn.access has propagate=False so it bypasses the root handler
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = [handler]


def setup_tracing() -> None:
    """Configure OTLP export and JSON logging if OTEL_EXPORTER_OTLP_ENDPOINT is set."""
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return

    resource = Resource.create({SERVICE_NAME: _SERVICE})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    LoggingInstrumentor().instrument()
    _configure_json_logging()
