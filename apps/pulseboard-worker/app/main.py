"""PulseBoard worker entry point."""

import logging
import os

from app.worker import run

_LOG_FMT = (
    '{"time": "%(asctime)s", "level": "%(levelname)s",'
    ' "service": "pulseboard-worker", "msg": "%(message)s"}'
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=_LOG_FMT,
)

if __name__ == "__main__":
    run()
