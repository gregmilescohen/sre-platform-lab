"""Unit tests for app.telemetry — JSON log formatter and tracing setup."""

import json
import logging
from unittest.mock import MagicMock, patch

from app.telemetry import _configure_json_logging, _JsonFormatter, setup_tracing

# ---------------------------------------------------------------------------
# _JsonFormatter
# ---------------------------------------------------------------------------


def _make_record(
    message: str = "hello world",
    level: int = logging.INFO,
    name: str = "test.logger",
    **extra: object,
) -> logging.LogRecord:
    """Return a LogRecord with optional extra attributes set."""
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


class TestJsonFormatter:
    """Tests for _JsonFormatter."""

    def setup_method(self) -> None:
        """Instantiate a fresh formatter before each test."""
        self.formatter = _JsonFormatter()

    def test_output_is_valid_json(self) -> None:
        """format() returns a string that parses as a JSON object."""
        record = _make_record()
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self) -> None:
        """format() includes message, logger, level, service, and time fields."""
        record = _make_record("test message", name="my.logger")
        parsed = json.loads(self.formatter.format(record))
        assert parsed["message"] == "test message"
        assert parsed["logger"] == "my.logger"
        assert parsed["level"] == "INFO"
        assert parsed["service"] == "pulseboard-api"
        assert "time" in parsed

    def test_no_trace_fields_without_otel(self) -> None:
        """format() omits trace_id and span_id when OTel attributes are absent."""
        record = _make_record()
        parsed = json.loads(self.formatter.format(record))
        assert "trace_id" not in parsed
        assert "span_id" not in parsed

    def test_trace_fields_included_when_otel_present(self) -> None:
        """format() includes trace_id and span_id when OTel injects them."""
        trace_id = "a" * 32
        span_id = "b" * 16
        record = _make_record(otelTraceID=trace_id, otelSpanID=span_id)
        parsed = json.loads(self.formatter.format(record))
        assert parsed["trace_id"] == trace_id
        assert parsed["span_id"] == span_id

    def test_zero_trace_id_omitted(self) -> None:
        """format() omits trace_id when the OTel trace ID is all zeros (no active span)."""
        record = _make_record(otelTraceID="0" * 32, otelSpanID="0" * 16)
        parsed = json.loads(self.formatter.format(record))
        assert "trace_id" not in parsed

    def test_newlines_in_message_are_json_escaped(self) -> None:
        """format() produces a single-line JSON string even when message contains newlines."""
        record = _make_record("line1\nline2")
        output = self.formatter.format(record)
        assert output.count("\n") == 0
        parsed = json.loads(output)
        assert "\n" in parsed["message"]

    def test_level_name_reflects_record_level(self) -> None:
        """format() uses the record's level name, not a hardcoded value."""
        record = _make_record(level=logging.ERROR)
        parsed = json.loads(self.formatter.format(record))
        assert parsed["level"] == "ERROR"


# ---------------------------------------------------------------------------
# _configure_json_logging
# ---------------------------------------------------------------------------


class TestConfigureJsonLogging:
    """Tests for _configure_json_logging."""

    def test_replaces_root_handler_with_json_formatter(self) -> None:
        """_configure_json_logging installs a single handler with _JsonFormatter on root."""
        _configure_json_logging()
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, _JsonFormatter)

    def test_sets_root_level_to_info(self) -> None:
        """_configure_json_logging sets the root logger level to INFO."""
        _configure_json_logging()
        assert logging.getLogger().level == logging.INFO

    def test_uvicorn_access_handler_replaced(self) -> None:
        """_configure_json_logging also replaces the uvicorn.access handler."""
        _configure_json_logging()
        uvicorn_access = logging.getLogger("uvicorn.access")
        assert len(uvicorn_access.handlers) == 1
        assert isinstance(uvicorn_access.handlers[0].formatter, _JsonFormatter)


# ---------------------------------------------------------------------------
# setup_tracing
# ---------------------------------------------------------------------------


class TestSetupTracing:
    """Tests for setup_tracing."""

    def test_no_op_when_env_var_unset(self) -> None:
        """setup_tracing does nothing when OTEL_EXPORTER_OTLP_ENDPOINT is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("app.telemetry.TracerProvider") as mock_provider:
                setup_tracing()
                mock_provider.assert_not_called()

    def test_configures_tracer_provider_when_endpoint_set(self) -> None:
        """setup_tracing wires up TracerProvider, exporter, and LoggingInstrumentor."""
        env = {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector:4317"}
        with patch.dict("os.environ", env):
            with (
                patch("app.telemetry.TracerProvider") as mock_provider,
                patch("app.telemetry.OTLPSpanExporter"),
                patch("app.telemetry.BatchSpanProcessor"),
                patch("app.telemetry.trace.set_tracer_provider"),
                patch("app.telemetry.LoggingInstrumentor") as mock_instrumentor,
                patch("app.telemetry._configure_json_logging") as mock_configure,
            ):
                mock_provider_instance = MagicMock()
                mock_provider.return_value = mock_provider_instance

                setup_tracing()

                mock_provider.assert_called_once()
                mock_provider_instance.add_span_processor.assert_called_once()
                mock_instrumentor.return_value.instrument.assert_called_once()
                mock_configure.assert_called_once()
