"""Prometheus metrics for pulseboard-api.

RED metrics:
  - Rate:   pulseboard_api_requests_total
  - Errors: captured via status_code label (5xx)
  - Duration: pulseboard_api_request_duration_seconds
"""

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "pulseboard_api_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "pulseboard_api_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)


def record_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """Record a single HTTP request in the RED metrics counters.

    Args:
        method: HTTP method (e.g. GET, POST).
        endpoint: Request path (e.g. /health).
        status_code: HTTP response status code.
        duration: Request duration in seconds.
    """
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
