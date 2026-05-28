from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import LOGS_DIR, ensure_user_dirs


def configure_logging(debug: bool = False) -> logging.Logger:
    ensure_user_dirs()
    logger = logging.getLogger("openlaunchdeck")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOGS_DIR / "openlaunchdeck.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.WARNING)
    logger.addHandler(stream_handler)
    return logger
