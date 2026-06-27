"""Alertmanager query tool — used by the webhook service for pre/post incident checks."""

import os

import httpx

ALERTMANAGER_URL = os.getenv("ALERTMANAGER_URL", "http://localhost:9093")


def get_active_alerts(service: str | None = None) -> list[dict]:
    """Fetch currently firing and pending alerts from Alertmanager.

    Args:
        service: Optional label filter — only return alerts for this service.

    Returns:
        List of normalised alert dicts. Critical alerts sorted first.
    """
    resp = httpx.get(
        f"{ALERTMANAGER_URL}/api/v2/alerts",
        params={"active": "true", "silenced": "false", "inhibited": "false"},
        timeout=10,
    )
    resp.raise_for_status()

    alerts: list[dict] = []
    for alert in resp.json():
        labels = alert.get("labels", {})
        if service and labels.get("service") != service:
            continue
        annotations = alert.get("annotations", {})
        alerts.append(
            {
                "alertname": labels.get("alertname", "unknown"),
                "severity": labels.get("severity", "unknown"),
                "service": labels.get("service", "unknown"),
                "slo": labels.get("slo"),
                "state": alert.get("state", "unknown"),
                "summary": annotations.get("summary", ""),
                "description": annotations.get("description", ""),
                "active_since": alert.get("activeAt", ""),
                "runbook_url": annotations.get("runbook_url"),
            }
        )

    return sorted(alerts, key=lambda a: a["severity"] != "critical")
