"""Synthetic event generator for the PulseBoard demo workload.

Simulates client-side activity by POSTing randomised events to the
pulseboard-api POST /events endpoint at a configurable rate. This keeps
all traffic observable through the API's RED metrics and OTel traces.

EVENT_TYPES are weighted so error events are rarer than page_view events,
producing a realistic traffic distribution.
"""

import json
import logging
import os
import random
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

EVENT_TYPES: list[str] = [
    "page_view",
    "button_click",
    "api_call",
    "search",
    "checkout",
    "login",
    "error",
]

_WEIGHTS: list[int] = [30, 20, 20, 10, 5, 10, 5]


def build_event(event_name: str) -> dict:
    """Build a single synthetic event payload matching the EmitRequest schema.

    Args:
        event_name: The event type from EVENT_TYPES.

    Returns:
        A dict with event_name and metadata, ready to POST as JSON.
    """
    return {
        "event_name": event_name,
        "metadata": {
            "session_id": str(uuid.uuid4()),
            "user_agent": random.choice(
                [
                    "Mozilla/5.0 Chrome/120",
                    "Mozilla/5.0 Firefox/121",
                    "Mozilla/5.0 Safari/17",
                ]
            ),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
            "emitted_at": datetime.now(UTC).isoformat(),
        },
    }


def publish_batch(api_url: str, batch_size: int = 5) -> tuple[int, int]:
    """POST a batch of synthetic events to the API.

    Args:
        api_url: Base URL of the pulseboard-api (e.g. http://pulseboard-api:8080).
        batch_size: Number of events to POST in this batch.

    Returns:
        Tuple of (ok_count, error_count).
    """
    ok = err = 0
    for _ in range(batch_size):
        event_name = random.choices(EVENT_TYPES, weights=_WEIGHTS, k=1)[0]
        body = json.dumps(build_event(event_name)).encode()
        req = urllib.request.Request(
            f"{api_url}/events/",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                ok += 1
        except urllib.error.URLError as exc:
            logger.error("Failed to emit event %s: %s", event_name, exc)
            err += 1
    return ok, err


def run() -> None:
    """Main publish loop — runs until process is killed."""
    interval = float(os.getenv("PUBLISH_INTERVAL_SECONDS", "1.0"))
    batch_size = int(os.getenv("BATCH_SIZE", "5"))
    api_url = os.getenv("PULSEBOARD_API_URL", "http://localhost:8080")

    logger.info(
        "Worker started. interval=%.1fs batch=%d api=%s",
        interval,
        batch_size,
        api_url,
    )

    while True:
        ok, err = publish_batch(api_url, batch_size=batch_size)
        logger.info("Emitted batch ok=%d errors=%d", ok, err)
        open("/tmp/worker.heartbeat", "w").close()
        time.sleep(interval)
