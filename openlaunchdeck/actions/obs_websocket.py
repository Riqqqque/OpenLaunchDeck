from __future__ import annotations

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

from .base import ActionResult, BaseAction


OBS_OPERATIONS = [
    "save_replay_buffer",
    "start_replay_buffer",
    "stop_replay_buffer",
    "start_recording",
    "stop_recording",
    "start_streaming",
    "stop_streaming",
    "switch_scene",
    "toggle_input_mute",
]


@dataclass(slots=True)
class ObsRequestResult:
    ok: bool
    data: dict[str, Any]
    comment: str = ""


class ObsWebSocketClient:
    def __init__(self, host: str, port: int, password: str = "", timeout: float = 3.0) -> None:
        self.host = host or "127.0.0.1"
        self.port = int(port or 4455)
        self.password = password or ""
        self.timeout = max(0.5, float(timeout or 3.0))
        self._socket = None

    def __enter__(self) -> "ObsWebSocketClient":
        try:
            import websocket
        except Exception as exc:
            raise RuntimeError("Install websocket-client to use OBS WebSocket actions.") from exc
        self._socket = websocket.create_connection(f"ws://{self.host}:{self.port}", timeout=self.timeout)
        hello = self._receive()
        if int(hello.get("op", -1)) != 0:
            raise RuntimeError("OBS WebSocket did not send a hello message.")
        authentication = dict(hello.get("d", {}).get("authentication") or {})
        identify: dict[str, Any] = {"rpcVersion": 1}
        if authentication:
            if not self.password:
                raise RuntimeError("OBS WebSocket password is required.")
            identify["authentication"] = build_obs_auth_response(
                self.password,
                str(authentication.get("salt") or ""),
                str(authentication.get("challenge") or ""),
            )
        self._send({"op": 1, "d": identify})
        identified = self._receive()
        if int(identified.get("op", -1)) != 2:
            raise RuntimeError("OBS WebSocket authentication failed.")
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def request(self, request_type: str, request_data: dict[str, Any] | None = None) -> ObsRequestResult:
        request_id = str(uuid.uuid4())
        self._send(
            {
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId": request_id,
                    "requestData": request_data or {},
                },
            }
        )
        while True:
            message = self._receive()
            if int(message.get("op", -1)) != 7:
                continue
            data = dict(message.get("d") or {})
            if data.get("requestId") != request_id:
                continue
            status = dict(data.get("requestStatus") or {})
            return ObsRequestResult(
                ok=bool(status.get("result")),
                data=dict(data.get("responseData") or {}),
                comment=str(status.get("comment") or ""),
            )

    def _send(self, message: dict[str, Any]) -> None:
        if self._socket is None:
            raise RuntimeError("OBS WebSocket is not connected.")
        self._socket.send(json.dumps(message, separators=(",", ":")))

    def _receive(self) -> dict[str, Any]:
        if self._socket is None:
            raise RuntimeError("OBS WebSocket is not connected.")
        raw = self._socket.recv()
        try:
            message = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OBS WebSocket returned invalid JSON.") from exc
        if not isinstance(message, dict):
            raise RuntimeError("OBS WebSocket returned an invalid message.")
        return message


def build_obs_auth_response(password: str, salt: str, challenge: str) -> str:
    secret = base64.b64encode(hashlib.sha256((password + salt).encode("utf-8")).digest()).decode("utf-8")
    return base64.b64encode(hashlib.sha256((secret + challenge).encode("utf-8")).digest()).decode("utf-8")


class ObsWebSocketAction(BaseAction):
    type_name = "obs_websocket"
    display_name = "OBS WebSocket"
    description = "Control OBS through the built-in OBS WebSocket server."
    config_fields = [
        {"name": "operation", "label": "Operation", "type": "choice", "choices": OBS_OPERATIONS},
        {"name": "host", "label": "Host", "type": "text"},
        {"name": "port", "label": "Port", "type": "number"},
        {"name": "password", "label": "Password", "type": "text"},
        {"name": "scene_name", "label": "Scene Name", "type": "text"},
        {"name": "input_name", "label": "Input Name", "type": "text"},
        {"name": "start_if_stopped", "label": "Start Replay Buffer If Needed", "type": "bool"},
        {"name": "timeout_ms", "label": "Timeout Ms", "type": "number"},
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        operation = str(config.get("operation") or "").strip() or "save_replay_buffer"
        host = str(config.get("host") or "127.0.0.1").strip()
        port = int(config.get("port") or 4455)
        password = str(config.get("password") or "")
        timeout_ms = int(config.get("timeout_ms") or 3000)
        try:
            with ObsWebSocketClient(host, port, password, timeout_ms / 1000.0) as client:
                return run_obs_operation(client, operation, config)
        except Exception as exc:
            if context.logger:
                context.logger.warning("OBS WebSocket action failed: %s", exc)
            return ActionResult.fail(f"OBS WebSocket failed: {exc}")


def run_obs_operation(client: ObsWebSocketClient, operation: str, config: dict) -> ActionResult:
    if operation == "save_replay_buffer":
        status = client.request("GetReplayBufferStatus")
        if not status.ok:
            return _obs_fail("Could not read replay buffer status.", status)
        if not bool(status.data.get("outputActive")):
            if bool(config.get("start_if_stopped", True)):
                started = client.request("StartReplayBuffer")
                if not started.ok:
                    return _obs_fail("Could not start replay buffer.", started)
                return ActionResult.ok("Replay buffer started. Press again to save a clip.")
            return ActionResult.fail("Replay buffer is not running.")
        saved = client.request("SaveReplayBuffer")
        if not saved.ok:
            return _obs_fail("Could not save replay buffer.", saved)
        return ActionResult.ok("Replay buffer save requested.")
    if operation == "start_replay_buffer":
        return _simple_request(client, "StartReplayBuffer", "Replay buffer started.")
    if operation == "stop_replay_buffer":
        return _simple_request(client, "StopReplayBuffer", "Replay buffer stopped.")
    if operation == "start_recording":
        return _simple_request(client, "StartRecord", "Recording started.")
    if operation == "stop_recording":
        return _simple_request(client, "StopRecord", "Recording stopped.")
    if operation == "start_streaming":
        return _simple_request(client, "StartStream", "Streaming started.")
    if operation == "stop_streaming":
        return _simple_request(client, "StopStream", "Streaming stopped.")
    if operation == "switch_scene":
        scene_name = str(config.get("scene_name") or "").strip()
        if not scene_name:
            return ActionResult.fail("Scene name is required.")
        return _simple_request(client, "SetCurrentProgramScene", f"Switched to scene {scene_name}.", {"sceneName": scene_name})
    if operation == "toggle_input_mute":
        input_name = str(config.get("input_name") or "").strip()
        if not input_name:
            return ActionResult.fail("Input name is required.")
        return _simple_request(client, "ToggleInputMute", f"Toggled mute for {input_name}.", {"inputName": input_name})
    return ActionResult.fail(f"Unknown OBS operation: {operation}")


def _simple_request(client: ObsWebSocketClient, request_type: str, message: str, data: dict[str, Any] | None = None) -> ActionResult:
    result = client.request(request_type, data)
    if not result.ok:
        return _obs_fail(message, result)
    return ActionResult.ok(message)


def _obs_fail(message: str, result: ObsRequestResult) -> ActionResult:
    details = f" {result.comment}" if result.comment else ""
    return ActionResult.fail(f"{message}{details}".strip())
