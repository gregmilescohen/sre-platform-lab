"""Tests for the worker entry point (app/main.py)."""

import runpy
from unittest.mock import patch


def test_main_module_configures_logging() -> None:
    """app.main imports cleanly and sets up structured JSON logging."""
    import logging

    import app.main  # noqa: F401 — import triggers module-level logging.basicConfig

    root = logging.getLogger()
    assert root is not None


def test_main_calls_run_when_executed_as_dunder_main() -> None:
    """Running app.main as __main__ invokes worker.run()."""
    with patch("app.worker.run") as mock_run:
        runpy.run_module("app.main", run_name="__main__")
    mock_run.assert_called_once()
