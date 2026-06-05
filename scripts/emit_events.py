#!/usr/bin/env python3
"""Continuously emit random events to the PulseBoard API via POST /events.

Runs until killed (Ctrl-C or process signal). Started automatically by
`make up` once the API is healthy. Uses only stdlib so no install is needed.

Usage:
    python3 scripts/emit_events.py [--url URL] [--rate N] [--batch N]

Options:
    --url    Base URL of the API          (default: http://localhost:8080)
    --rate   Seconds between batches      (default: 1.0)
    --batch  Events per batch             (default: 3)
"""

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime

EVENT_TYPES = ["page_view", "button_click", "api_call", "search", "checkout", "login", "error"]
_WEIGHTS = [30, 20, 20, 10, 5, 10, 5]


def _build_payload(event_name: str) -> dict:
    return {
        "event_name": event_name,
        "metadata": {
            "session_id": str(uuid.uuid4()),
            "user_agent": random.choice([
                "Mozilla/5.0 Chrome/120",
                "Mozilla/5.0 Firefox/121",
                "Mozilla/5.0 Safari/17",
            ]),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
            "emitted_at": datetime.now(UTC).isoformat(),
        },
    }


def emit_batch(url: str, batch_size: int) -> tuple[int, int]:
    """POST a batch of events. Returns (ok_count, error_count)."""
    ok = err = 0
    for _ in range(batch_size):
        event_name = random.choices(EVENT_TYPES, weights=_WEIGHTS, k=1)[0]
        body = json.dumps(_build_payload(event_name)).encode()
        req = urllib.request.Request(
            f"{url}/events/",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5):
                ok += 1
        except urllib.error.URLError:
            err += 1
    return ok, err


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--rate", type=float, default=1.0, metavar="SECONDS")
    parser.add_argument("--batch", type=int, default=3, metavar="N")
    args = parser.parse_args()

    print(f"[emit_events] Emitting {args.batch} events/batch every {args.rate}s → {args.url}", flush=True)
    total_ok = total_err = 0

    while True:
        ok, err = emit_batch(args.url, args.batch)
        total_ok += ok
        total_err += err
        if err:
            print(f"[emit_events] ok={total_ok} errors={total_err}", flush=True)
        time.sleep(args.rate)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
