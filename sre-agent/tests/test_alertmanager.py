"""Tests for the Alertmanager query tool."""

from unittest.mock import MagicMock, patch

from agent.tools.alertmanager import get_active_alerts


def _raw_alert(name: str, severity: str) -> dict:
    return {
        "labels": {"alertname": name, "severity": severity, "service": "pulseboard-api"},
        "annotations": {"summary": f"{name} summary", "description": "desc"},
        "state": "firing",
        "activeAt": "2024-01-01T00:00:00Z",
        "endsAt": "0001-01-01T00:00:00Z",
    }


@patch("agent.tools.alertmanager.httpx.get")
def test_get_active_alerts_normalises_fields(mock_get: MagicMock) -> None:
    """get_active_alerts returns flat dicts with expected keys."""
    mock_get.return_value.json.return_value = [
        _raw_alert("PulseBoardHighErrorRateFast", "critical")
    ]
    mock_get.return_value.raise_for_status = MagicMock()

    alerts = get_active_alerts()
    assert len(alerts) == 1
    assert alerts[0]["alertname"] == "PulseBoardHighErrorRateFast"
    assert alerts[0]["severity"] == "critical"


@patch("agent.tools.alertmanager.httpx.get")
def test_get_active_alerts_empty_when_quiet(mock_get: MagicMock) -> None:
    """get_active_alerts returns empty list when no alerts are firing."""
    mock_get.return_value.json.return_value = []
    mock_get.return_value.raise_for_status = MagicMock()

    assert get_active_alerts() == []


@patch("agent.tools.alertmanager.httpx.get")
def test_get_active_alerts_filters_by_service(mock_get: MagicMock) -> None:
    """get_active_alerts filters correctly when service is specified."""
    mock_get.return_value.json.return_value = [
        _raw_alert("AlertA", "critical"),
        {
            "labels": {"alertname": "AlertB", "severity": "warning", "service": "other-service"},
            "annotations": {},
            "state": "firing",
            "activeAt": "",
            "endsAt": "",
        },
    ]
    mock_get.return_value.raise_for_status = MagicMock()

    alerts = get_active_alerts(service="pulseboard-api")
    assert len(alerts) == 1
    assert alerts[0]["alertname"] == "AlertA"
