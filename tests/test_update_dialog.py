import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.services.update_service import UpdateService
from openlaunchdeck.ui.update_dialog import UpdateCheckWorker


class FailingUpdateService(UpdateService):
    def __init__(self):
        super().__init__("0.1.0")

    def fetch_manifest(self, manifest_url: str):
        raise RuntimeError("manifest unavailable")


def test_update_worker_reports_failed_check_without_raising():
    QApplication.instance() or QApplication([])
    worker = UpdateCheckWorker(FailingUpdateService(), "https://example.invalid/update.json")
    failures = []
    worker.failed.connect(failures.append)

    worker.run()

    assert failures == ["manifest unavailable"]
