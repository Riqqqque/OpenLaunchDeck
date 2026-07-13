from __future__ import annotations

import hashlib
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QIODevice, QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "OpenLaunchDeck.Rique.SingleInstance"
COMMAND_SHOW = "show"
COMMAND_BACKGROUND = "background"


@dataclass(frozen=True, slots=True)
class LaunchOptions:
    command: str = COMMAND_SHOW
    start_minimized_override: bool | None = None


def parse_launch_options(argv: Sequence[str]) -> LaunchOptions:
    args = {arg.lower() for arg in argv[1:]}
    if "--background" in args or "--start-minimized" in args:
        return LaunchOptions(command=COMMAND_BACKGROUND, start_minimized_override=True)
    if "--show" in args or "--focus" in args:
        return LaunchOptions(command=COMMAND_SHOW, start_minimized_override=False)
    return LaunchOptions()


def _command_file_path(server_name: str) -> Path:
    digest = hashlib.sha256(server_name.encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"openlaunchdeck-{digest}.cmd"


def _write_pending_command(server_name: str, command: str) -> None:
    try:
        _command_file_path(server_name).write_text(command, encoding="utf-8")
    except OSError:
        pass


def _read_pending_command(server_name: str) -> str:
    path = _command_file_path(server_name)
    try:
        command = path.read_text(encoding="utf-8").strip()
    except OSError:
        command = ""
    try:
        path.unlink()
    except OSError:
        pass
    return command


def _remove_pending_command(server_name: str) -> None:
    try:
        _command_file_path(server_name).unlink()
    except OSError:
        pass


def notify_existing_instance(command: str, server_name: str = SERVER_NAME, timeout_ms: int = 600) -> bool:
    clean_command = command.strip() or COMMAND_SHOW
    _write_pending_command(server_name, clean_command)
    socket = QLocalSocket()
    socket.connectToServer(server_name, QIODevice.OpenModeFlag.ReadWrite)
    if not socket.waitForConnected(timeout_ms):
        socket.abort()
        _remove_pending_command(server_name)
        return False
    payload = f"{clean_command}\n".encode("utf-8")
    socket.write(payload)
    socket.flush()
    socket.waitForBytesWritten(timeout_ms)
    socket.waitForDisconnected(100)
    socket.disconnectFromServer()
    return True


class SingleInstanceServer(QObject):
    def __init__(self, parent: QObject | None = None, server_name: str = SERVER_NAME, logger: object | None = None) -> None:
        super().__init__(parent)
        self.server_name = server_name
        self.logger = logger
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_new_connection)
        self._command_handler: Callable[[str], None] | None = None
        self._pending_commands: list[str] = []
        self._sockets: list[QLocalSocket] = []

    def listen(self) -> bool:
        if self.server.listen(self.server_name):
            return True
        QLocalServer.removeServer(self.server_name)
        if self.server.listen(self.server_name):
            return True
        if self.logger:
            self.logger.warning("Could not start single-instance server: %s", self.server.errorString())
        return False

    def set_logger(self, logger: object) -> None:
        self.logger = logger

    def set_command_handler(self, command_handler: Callable[[str], None]) -> None:
        self._command_handler = command_handler
        pending = list(self._pending_commands)
        self._pending_commands.clear()
        for command in pending:
            self._dispatch(command)

    def close(self) -> None:
        self.server.close()
        QLocalServer.removeServer(self.server_name)

    def _handle_new_connection(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            self._sockets.append(socket)
            socket.readyRead.connect(lambda socket=socket: self._read_socket(socket))
            QTimer.singleShot(1000, lambda socket=socket: self._read_socket(socket, fallback=True))
            if socket.bytesAvailable():
                self._read_socket(socket)

    def _read_socket(self, socket: QLocalSocket, fallback: bool = False) -> None:
        if socket not in self._sockets:
            return
        if not socket.bytesAvailable() and not fallback:
            return
        data = bytes(socket.readAll()).decode("utf-8", errors="replace").strip()
        command = data or _read_pending_command(self.server_name) or COMMAND_SHOW
        if data:
            _remove_pending_command(self.server_name)
        self._sockets.remove(socket)
        socket.disconnectFromServer()
        socket.deleteLater()
        self._dispatch(command)

    def _dispatch(self, command: str) -> None:
        if self._command_handler is None:
            self._pending_commands.append(command)
            return
        self._command_handler(command)
