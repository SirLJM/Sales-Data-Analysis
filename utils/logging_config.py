from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logging(level: int | None = None) -> logging.Logger:
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = LOG_LEVELS.get(env_level, logging.INFO)

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("stockmonitor")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"stockmonitor.{name}")
