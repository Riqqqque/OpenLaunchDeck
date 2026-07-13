from __future__ import annotations

import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import SimpleQueue

from .paths import LOGS_DIR, ensure_user_dirs


def configure_logging(debug: bool = False) -> logging.Logger:
    ensure_user_dirs()
    logger = logging.getLogger("openlaunchdeck")
    shutdown_logging(logger)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

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
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.WARNING)

    log_queue: SimpleQueue[logging.LogRecord] = SimpleQueue()
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    listener = QueueListener(log_queue, file_handler, stream_handler, respect_handler_level=True)
    listener.start()
    logger.addHandler(queue_handler)
    logger._openlaunchdeck_listener = listener  # type: ignore[attr-defined]
    logger._openlaunchdeck_output_handlers = (file_handler, stream_handler)  # type: ignore[attr-defined]
    return logger


def shutdown_logging(logger: logging.Logger | None) -> None:
    if logger is None:
        return
    listener = getattr(logger, "_openlaunchdeck_listener", None)
    if listener is not None:
        try:
            listener.stop()
        finally:
            delattr(logger, "_openlaunchdeck_listener")
    handlers = getattr(logger, "_openlaunchdeck_output_handlers", ())
    for handler in handlers:
        handler.close()
    if hasattr(logger, "_openlaunchdeck_output_handlers"):
        delattr(logger, "_openlaunchdeck_output_handlers")
