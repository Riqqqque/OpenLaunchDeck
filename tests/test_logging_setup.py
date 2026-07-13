import logging
from logging.handlers import QueueHandler

import openlaunchdeck.logging_setup as logging_setup


def test_file_logging_is_queued_and_flushes_on_shutdown(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOGS_DIR", tmp_path)
    logger = logging_setup.configure_logging()

    try:
        assert any(isinstance(handler, QueueHandler) for handler in logger.handlers)
        logger.info("queued log message")
    finally:
        logging_setup.shutdown_logging(logger)

    text = (tmp_path / "openlaunchdeck.log").read_text(encoding="utf-8")
    assert "queued log message" in text
    assert logger.level == logging.INFO
