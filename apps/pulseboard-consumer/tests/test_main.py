"""Tests for the consumer entry point (app/main.py)."""

import runpy
import sys
from unittest.mock import patch


def test_main_module_configures_logging() -> None:
    """Importing app.main configures the root logger."""
    import logging

    import app.main  # noqa: F401

    root = logging.getLogger()
    assert root is not None


def test_main_calls_run_when_executed_as_dunder_main() -> None:
    """Running app.main as __main__ calls run_subscriber."""
    sys.modules.pop("app.main", None)
    with patch("app.consumer.run_subscriber") as mock_run:
        with patch("app.db.create_tables"):
            with patch("prometheus_client.start_http_server"):
                runpy.run_module("app.main", run_name="__main__")
    mock_run.assert_called_once()
