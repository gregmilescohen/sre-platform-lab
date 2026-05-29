"""Google Cloud Pub/Sub publisher helpers.

When PUBSUB_EMULATOR_HOST is set, the google-cloud-pubsub library automatically
routes requests to the local emulator — no code changes needed.

Environment variables:
  PUBSUB_EMULATOR_HOST  e.g. localhost:8085 or pubsub-emulator:8085 (in k8s)
  PUBSUB_PROJECT_ID     default: pulseboard
  PUBSUB_TOPIC_ID       default: pulseboard-events
"""

import functools
import json
import os
from datetime import UTC, datetime

from google.cloud import pubsub_v1


@functools.lru_cache(maxsize=1)
def get_publisher() -> pubsub_v1.PublisherClient:
    """Return the application-scoped Pub/Sub publisher client (singleton).

    The client automatically connects to the emulator when PUBSUB_EMULATOR_HOST is set.
    Used as a FastAPI dependency so it can be overridden in tests.
    """
    return pubsub_v1.PublisherClient()


def get_topic_path(publisher: pubsub_v1.PublisherClient) -> str:
    """Return the fully-qualified Pub/Sub topic path for this service.

    Args:
        publisher: The Pub/Sub publisher client.

    Returns:
        The fully-qualified topic path string.
    """
    project_id = os.getenv("PUBSUB_PROJECT_ID", "pulseboard")
    topic_id = os.getenv("PUBSUB_TOPIC_ID", "pulseboard-events")
    return publisher.topic_path(project_id, topic_id)


def publish_event(
    event_name: str,
    metadata: dict,
    publisher: pubsub_v1.PublisherClient,
) -> str:
    """Publish a single event to the Pub/Sub topic.

    Returns the Pub/Sub message ID on success.
    Blocks until the publish is acknowledged by the server (or emulator).
    """
    topic_path = get_topic_path(publisher)
    payload = {
        "event_name": event_name,
        "metadata": metadata,
        "emitted_at": datetime.now(UTC).isoformat(),
    }
    data = json.dumps(payload).encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    return future.result()
