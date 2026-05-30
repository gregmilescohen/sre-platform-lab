"""PulseBoard Consumer — entry point."""

import logging
import os

from prometheus_client import start_http_server

from app.consumer import run_subscriber
from app.db import create_tables

_LOG_FMT = (
    '{"time": "%(asctime)s", "level": "%(levelname)s",'
    ' "service": "pulseboard-consumer", "msg": "%(message)s"}'
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=_LOG_FMT,
)

if __name__ == "__main__":
    metrics_port = int(os.getenv("METRICS_PORT", "9102"))
    start_http_server(metrics_port)
    create_tables()
    run_subscriber()
