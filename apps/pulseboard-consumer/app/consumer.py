"""Pub/Sub consumer logic.

Pulls messages from the pulseboard-events subscription in batches,
writes each event to event_log, then acks the messages.

Malformed messages (bad JSON, missing fields) are acked without a DB write
to avoid poison pills that would block the subscription indefinitely.

Environment variables:
  PUBSUB_EMULATOR_HOST     e.g. localhost:8085 or pubsub-emulator:8085 (in k8s)
  PUBSUB_PROJECT_ID        default: pulseboard
  PUBSUB_SUBSCRIPTION_ID   default: pulseboard-events-sub
  BATCH_SIZE               max messages per pull (default: 10)
  BATCH_TIMEOUT_SECONDS    sleep between pulls when queue is empty (default: 2)
"""

import json
import logging
import os
import time

from google.cloud import pubsub_v1
from sqlalchemy.orm import Session

from app.db import get_db
from app.metrics import BATCH_SIZE, MESSAGES_PROCESSED, PROCESSING_DURATION
from app.models import EventLog

logger = logging.getLogger(__name__)

_BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
_BATCH_TIMEOUT = float(os.getenv("BATCH_TIMEOUT_SECONDS", "2"))


def _build_subscription_path() -> str:
    """Return the full subscription resource path."""
    project_id = os.getenv("PUBSUB_PROJECT_ID", "pulseboard")
    subscription_id = os.getenv("PUBSUB_SUBSCRIPTION_ID", "pulseboard-events-sub")
    # Build path manually to avoid needing a client instance
    return f"projects/{project_id}/subscriptions/{subscription_id}"


def process_batch(
    messages: list[pubsub_v1.types.ReceivedMessage],
    db: Session,
) -> list[pubsub_v1.types.ReceivedMessage]:
    """Decode messages, write valid ones to event_log, return all messages to ack.

    All messages are returned for acking — including malformed ones — to prevent
    poison pills from blocking the subscription. Decode errors are logged.
    """
    BATCH_SIZE.observe(len(messages))
    rows = []
    for msg in messages:
        with PROCESSING_DURATION.time():
            try:
                payload = json.loads(msg.message.data.decode("utf-8"))
                rows.append(
                    EventLog(
                        event_name=payload["event_name"],
                        event_metadata=payload.get("metadata"),
                    )
                )
            except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as exc:
                logger.warning("Skipping malformed message %s: %s", msg.message.message_id, exc)
                MESSAGES_PROCESSED.labels(status="error").inc()

    if rows:
        for row in rows:
            db.add(row)
        db.commit()
        logger.info("Wrote %d event(s) to event_log", len(rows))
        MESSAGES_PROCESSED.labels(status="ok").inc(len(rows))

    return messages


def run_subscriber() -> None:
    """Main subscriber loop. Blocks indefinitely, pulling and processing messages."""
    subscription_path = _build_subscription_path()

    logger.info("Starting consumer. Subscription: %s", subscription_path)
    logger.info("Batch size: %d, timeout: %.1fs", _BATCH_SIZE, _BATCH_TIMEOUT)

    with pubsub_v1.SubscriberClient() as subscriber:
        while True:
            try:
                response = subscriber.pull(
                    request={
                        "subscription": subscription_path,
                        "max_messages": _BATCH_SIZE,
                    },
                    timeout=30,
                )
            except Exception as exc:
                logger.error("Pull failed: %s", exc)
                time.sleep(_BATCH_TIMEOUT)
                continue  # pragma: no cover

            if not response.received_messages:
                time.sleep(_BATCH_TIMEOUT)
                continue  # pragma: no cover

            db = get_db()
            try:
                to_ack = process_batch(response.received_messages, db)
            finally:
                db.close()

            ack_ids = [m.ack_id for m in to_ack]
            if ack_ids:
                subscriber.acknowledge(
                    request={"subscription": subscription_path, "ack_ids": ack_ids}
                )
                logger.debug("Acked %d message(s)", len(ack_ids))

            open("/tmp/consumer.heartbeat", "w").close()
