"""Tests for the Prometheus query tool."""

from unittest.mock import MagicMock, patch

import pytest
from agent.tools.prometheus import query_prometheus


def _vector_response(value: float) -> dict:
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [{"metric": {}, "value": [1716000000, str(value)]}],
        },
    }


@patch("agent.tools.prometheus.httpx.get")
def test_query_prometheus_returns_data(mock_get: MagicMock) -> None:
    """query_prometheus returns the data object on success."""
    mock_get.return_value.json.return_value = _vector_response(0.95)
    mock_get.return_value.raise_for_status = MagicMock()

    result = query_prometheus("up")
    assert result["resultType"] == "vector"
    assert float(result["result"][0]["value"][1]) == pytest.approx(0.95)


@patch("agent.tools.prometheus.httpx.get")
def test_query_prometheus_raises_on_error_status(mock_get: MagicMock) -> None:
    """query_prometheus raises ValueError when Prometheus returns status=error."""
    mock_get.return_value.json.return_value = {"status": "error", "error": "bad_data"}
    mock_get.return_value.raise_for_status = MagicMock()

    with pytest.raises(ValueError, match="Prometheus query error"):
        query_prometheus("bad{query")
