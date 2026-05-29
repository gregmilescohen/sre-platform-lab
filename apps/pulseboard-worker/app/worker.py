"""Synthetic event publisher for the PulseBoard demo workload.

Publishes randomised events to the pulseboard-events Pub/Sub topic at a
configurable rate. EVENT_TYPES are weighted so error events are rarer than
page_view events, producing a realistic traffic distribution.
"""

import json
import logging
import os
import random
import time
import uuid
from datetime import UTC, datetime

from google.cloud import pubsub_v1

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
    """Build a single synthetic event payload.

    Args:
        event_name: The event type from EVENT_TYPES.

    Returns:
        A dict with event_name, emitted_at, and metadata.
    """
    return {
        "event_name": event_name,
        "emitted_at": datetime.now(UTC).isoformat(),
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
        },
    }


def publish_batch(
    publisher: pubsub_v1.PublisherClient,
    topic_path: str,
    batch_size: int = 5,
) -> int:
    """Publish a batch of synthetic events.

    Args:
        publisher: Pub/Sub publisher client.
        topic_path: Fully-qualified topic path.
        batch_size: Number of events per batch.

    Returns:
        Number of events successfully published.
    """
    futures = []
    for _ in range(batch_size):
        event_name = random.choices(EVENT_TYPES, weights=_WEIGHTS, k=1)[0]
        data = json.dumps(build_event(event_name)).encode("utf-8")
        futures.append(publisher.publish(topic_path, data))

    published = 0
    for future in futures:
        try:
            future.result(timeout=10)
            published += 1
        except Exception as exc:
            logger.error("Publish failed: %s", exc)
    return published


def run() -> None:
    """Main publish loop — runs until process is killed."""
    interval = float(os.getenv("PUBLISH_INTERVAL_SECONDS", "1.0"))
    batch_size = int(os.getenv("BATCH_SIZE", "5"))
    project_id = os.getenv("PUBSUB_PROJECT_ID", "pulseboard")
    topic_id = os.getenv("PUBSUB_TOPIC_ID", "pulseboard-events")

    with pubsub_v1.PublisherClient() as publisher:
        topic_path = publisher.topic_path(project_id, topic_id)
        logger.info(
            "Worker started. interval=%.1fs batch=%d topic=%s",
            interval,
            batch_size,
            topic_path,
        )

        while True:
            published = publish_batch(publisher, topic_path, batch_size=batch_size)
            logger.info("Published %d events", published)
            # Touch heartbeat file for Docker HEALTHCHECK
            open("/tmp/worker.heartbeat", "w").close()
            time.sleep(interval)
