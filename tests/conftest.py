import logging
import os
import shutil
import tempfile


TEST_ROOT = tempfile.mkdtemp(prefix="openlaunchdeck-tests-")
TEST_DATA_DIR = os.path.join(TEST_ROOT, "OpenLaunchDeck")
os.environ["OPENLAUNCHDECK_DATA_DIR"] = TEST_DATA_DIR


def pytest_sessionfinish(session, exitstatus):
    from openlaunchdeck.logging_setup import shutdown_logging

    shutdown_logging(logging.getLogger("openlaunchdeck"))
    shutil.rmtree(TEST_ROOT, ignore_errors=True)
