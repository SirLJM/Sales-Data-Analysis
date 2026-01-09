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


def setup_logging(level: int | None = None, log_to_file: bool = False) -> logging.Logger:
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = LOG_LEVELS.get(env_level, logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_to_file or os.getenv("LOG_TO_FILE", "false").lower() == "true":
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "stockmonitor.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handlers.append(file_handler)

    console_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    for handler in handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            handler.setFormatter(
                logging.Formatter(console_format, datefmt="%H:%M:%S.%f")
            )

    logging.basicConfig(
        level=level,
        format=console_format,
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
    return logging.getLogger("stockmonitor")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"stockmonitor.{name}")
