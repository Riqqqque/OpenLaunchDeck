from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import threading
from typing import Any

from PySide6.QtCore import QCoreApplication, QObject, QThread, Qt, Signal, Slot


@dataclass(slots=True)
class _DispatchRequest:
    callback: Callable[[], Any]
    completed: threading.Event = field(default_factory=threading.Event)
    result: Any = None
    error: BaseException | None = None


class MainThreadDispatcher(QObject):
    requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.requested.connect(self._execute, Qt.ConnectionType.QueuedConnection)

    def call(self, callback: Callable[[], Any], timeout: float = 30.0) -> Any:
        app = QCoreApplication.instance()
        if app is None or QThread.currentThread() == self.thread():
            return callback()
        request = _DispatchRequest(callback)
        self.requested.emit(request)
        if not request.completed.wait(timeout=max(0.1, timeout)):
            raise TimeoutError("The main window did not process an action in time.")
        if request.error is not None:
            raise request.error
        return request.result

    @Slot(object)
    def _execute(self, request: _DispatchRequest) -> None:
        try:
            request.result = request.callback()
        except BaseException as exc:
            request.error = exc
        finally:
            request.completed.set()
