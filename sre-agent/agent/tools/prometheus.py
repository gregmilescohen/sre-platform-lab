"""Prometheus instant query tool — used to snapshot metric values for the incident prompt."""

import os

import httpx

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")


def query_prometheus(expr: str) -> dict:
    """Run an instant PromQL query.

    Args:
        expr: A valid PromQL expression.

    Returns:
        The Prometheus data object (resultType + result list).

    Raises:
        ValueError: If Prometheus returns status != 'success'.
    """
    resp = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": expr},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if body["status"] != "success":
        raise ValueError(f"Prometheus query error: {body.get('error', 'unknown')}")
    return body["data"]
