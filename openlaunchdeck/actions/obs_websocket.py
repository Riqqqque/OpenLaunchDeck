from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import ActionResult, BaseAction


OBS_OPERATIONS = [
    "save_replay_buffer",
    "start_replay_buffer",
    "stop_replay_buffer",
    "save_screenshot",
    "start_recording",
    "stop_recording",
    "start_streaming",
    "stop_streaming",
    "switch_scene",
    "show_source",
    "hide_source",
    "toggle_source",
    "mute_input",
    "unmute_input",
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
        {"name": "password", "label": "Password", "type": "password"},
        {"name": "scene_name", "label": "Scene Name", "type": "text"},
        {"name": "source_name", "label": "Source Name", "type": "text"},
        {"name": "input_name", "label": "Input Name", "type": "text"},
        {"name": "screenshot_source", "label": "Screenshot Source", "type": "text"},
        {"name": "screenshot_folder", "label": "Screenshot Folder", "type": "path"},
        {"name": "screenshot_format", "label": "Screenshot Format", "type": "choice", "choices": ["png", "jpg"]},
        {"name": "start_if_stopped", "label": "Start Replay Buffer If Needed", "type": "bool"},
        {"name": "replay_verify_timeout_ms", "label": "Replay Verify Timeout Ms", "type": "number"},
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
        before = client.request("GetLastReplayBufferReplay")
        before_path = str(before.data.get("savedReplayPath") or "") if before.ok else ""
        save_started = time.time()
        saved = client.request("SaveReplayBuffer")
        if not saved.ok:
            return _obs_fail("Could not save replay buffer.", saved)
        verify_value = config.get("replay_verify_timeout_ms")
        verify_timeout = 10000 if verify_value in (None, "") else int(verify_value)
        replay_path = _wait_for_replay_file(client, before_path, save_started, verify_timeout / 1000.0)
        if replay_path is None:
            return ActionResult.fail(
                "OBS accepted the replay save request, but no replay file appeared. Restart the OBS replay buffer and try again."
            )
        return ActionResult.ok(f"Replay saved: {replay_path.name}", replay_path=str(replay_path))
    if operation == "save_screenshot":
        return _save_screenshot(client, config)
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
    if operation == "show_source":
        return _set_source_enabled(client, config, True)
    if operation == "hide_source":
        return _set_source_enabled(client, config, False)
    if operation == "toggle_source":
        return _toggle_source_enabled(client, config)
    if operation == "mute_input":
        return _set_input_muted(client, config, True)
    if operation == "unmute_input":
        return _set_input_muted(client, config, False)
    if operation == "toggle_input_mute":
        input_name = str(config.get("input_name") or "").strip()
        if not input_name:
            return ActionResult.fail("Input name is required.")
        return _simple_request(client, "ToggleInputMute", f"Toggled mute for {input_name}.", {"inputName": input_name})
    return ActionResult.fail(f"Unknown OBS operation: {operation}")


def _save_screenshot(client: ObsWebSocketClient, config: dict) -> ActionResult:
    source_name = str(config.get("screenshot_source") or "").strip()
    if not source_name:
        scene = client.request("GetCurrentProgramScene")
        if not scene.ok:
            return _obs_fail("Could not read current OBS scene.", scene)
        source_name = str(scene.data.get("currentProgramSceneName") or "").strip()
    if not source_name:
        return ActionResult.fail("OBS screenshot source is required.")

    folder_text = str(config.get("screenshot_folder") or "").strip()
    folder = Path(folder_text).expanduser() if folder_text else _obs_record_directory(client)
    folder.mkdir(parents=True, exist_ok=True)
    image_format = str(config.get("screenshot_format") or "png").lower().strip()
    if image_format not in {"png", "jpg"}:
        image_format = "png"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = folder / f"Screenshot {timestamp}.{image_format}"
    result = client.request(
        "SaveSourceScreenshot",
        {
            "sourceName": source_name,
            "imageFormat": image_format,
            "imageFilePath": str(output_path),
        },
    )
    if not result.ok:
        return _obs_fail("Could not save OBS screenshot.", result)
    screenshot_path = _wait_for_file(output_path, 2.0)
    if screenshot_path is None:
        return ActionResult.fail("OBS accepted the screenshot request, but no screenshot file appeared.")
    return ActionResult.ok(f"Screenshot saved: {output_path.name}", screenshot_path=str(output_path))


def _set_input_muted(client: ObsWebSocketClient, config: dict, muted: bool) -> ActionResult:
    input_name = str(config.get("input_name") or "").strip()
    if not input_name:
        return ActionResult.fail("Input name is required.")
    result = client.request("SetInputMute", {"inputName": input_name, "inputMuted": muted})
    if not result.ok:
        return _obs_fail(f"Could not {'mute' if muted else 'unmute'} {input_name}.", result)
    status = client.request("GetInputMute", {"inputName": input_name})
    if not status.ok:
        return _obs_fail(f"Could not verify mute state for {input_name}.", status)
    actual = bool(status.data.get("inputMuted"))
    if actual != muted:
        state = "muted" if muted else "unmuted"
        return ActionResult.fail(f"OBS did not verify {input_name} as {state}.")
    return ActionResult.ok(f"{input_name} {'muted' if muted else 'unmuted'}.")


def _set_source_enabled(client: ObsWebSocketClient, config: dict, enabled: bool) -> ActionResult:
    scene_name_result = _configured_or_current_scene(client, config)
    if isinstance(scene_name_result, ActionResult):
        return scene_name_result
    scene_name = scene_name_result
    source_name = _configured_source_name(config)
    if not source_name:
        return ActionResult.fail("Source name is required.")
    item = _find_scene_item(client, scene_name, source_name)
    if isinstance(item, ActionResult):
        return item
    result = client.request(
        "SetSceneItemEnabled",
        {
            "sceneName": scene_name,
            "sceneItemId": item["id"],
            "sceneItemEnabled": enabled,
        },
    )
    if not result.ok:
        return _obs_fail(f"Could not {'show' if enabled else 'hide'} {source_name}.", result)
    verified = _scene_item_enabled(client, scene_name, item["id"])
    if isinstance(verified, ActionResult):
        return verified
    if verified != enabled:
        return ActionResult.fail(f"OBS did not verify {source_name} as {'visible' if enabled else 'hidden'}.")
    return ActionResult.ok(f"{source_name} {'shown' if enabled else 'hidden'}.")


def _toggle_source_enabled(client: ObsWebSocketClient, config: dict) -> ActionResult:
    scene_name_result = _configured_or_current_scene(client, config)
    if isinstance(scene_name_result, ActionResult):
        return scene_name_result
    scene_name = scene_name_result
    source_name = _configured_source_name(config)
    if not source_name:
        return ActionResult.fail("Source name is required.")
    item = _find_scene_item(client, scene_name, source_name)
    if isinstance(item, ActionResult):
        return item
    return _set_source_enabled(client, {**config, "scene_name": scene_name, "source_name": source_name}, not item["enabled"])


def _configured_or_current_scene(client: ObsWebSocketClient, config: dict) -> str | ActionResult:
    scene_name = str(config.get("scene_name") or "").strip()
    if scene_name:
        return scene_name
    scene = client.request("GetCurrentProgramScene")
    if not scene.ok:
        return _obs_fail("Could not read current OBS scene.", scene)
    scene_name = str(scene.data.get("currentProgramSceneName") or "").strip()
    if not scene_name:
        return ActionResult.fail("Scene name is required.")
    return scene_name


def _configured_source_name(config: dict) -> str:
    return str(config.get("source_name") or config.get("input_name") or config.get("screenshot_source") or "").strip()


def _find_scene_item(client: ObsWebSocketClient, scene_name: str, source_name: str) -> dict[str, Any] | ActionResult:
    by_id = client.request("GetSceneItemId", {"sceneName": scene_name, "sourceName": source_name, "searchOffset": 0})
    if by_id.ok and "sceneItemId" in by_id.data:
        item_id = int(by_id.data["sceneItemId"])
        enabled = _scene_item_enabled(client, scene_name, item_id)
        if isinstance(enabled, ActionResult):
            return enabled
        return {"id": item_id, "enabled": enabled}

    items = client.request("GetSceneItemList", {"sceneName": scene_name})
    if not items.ok:
        return _obs_fail(f"Could not find source {source_name}.", items)
    for item in items.data.get("sceneItems", []):
        if str(item.get("sourceName") or "") == source_name:
            return {
                "id": int(item.get("sceneItemId")),
                "enabled": bool(item.get("sceneItemEnabled")),
            }
    return ActionResult.fail(f"Source {source_name} was not found in scene {scene_name}.")


def _scene_item_enabled(client: ObsWebSocketClient, scene_name: str, scene_item_id: int) -> bool | ActionResult:
    status = client.request("GetSceneItemEnabled", {"sceneName": scene_name, "sceneItemId": scene_item_id})
    if not status.ok:
        return _obs_fail("Could not verify source visibility.", status)
    return bool(status.data.get("sceneItemEnabled"))


def _obs_record_directory(client: ObsWebSocketClient) -> Path:
    result = client.request("GetRecordDirectory")
    if result.ok:
        folder = str(result.data.get("recordDirectory") or "").strip()
        if folder:
            return Path(folder)
    return Path.home() / "Videos"


def _wait_for_replay_file(client: ObsWebSocketClient, before_path: str, save_started: float, timeout_seconds: float) -> Path | None:
    deadline = time.time() + max(0.0, timeout_seconds)
    before_key = _path_key(before_path)
    while time.time() <= deadline:
        current = client.request("GetLastReplayBufferReplay")
        if current.ok:
            replay_path = Path(str(current.data.get("savedReplayPath") or ""))
            if replay_path.exists():
                try:
                    modified_at = replay_path.stat().st_mtime
                except OSError:
                    modified_at = 0
                if _path_key(str(replay_path)) != before_key or modified_at >= save_started - 1:
                    return replay_path
        time.sleep(0.5)
    return None


def _wait_for_file(path: Path, timeout_seconds: float) -> Path | None:
    deadline = time.time() + max(0.0, timeout_seconds)
    while time.time() <= deadline:
        try:
            if path.exists() and path.stat().st_size > 0:
                return path
        except OSError:
            pass
        time.sleep(0.1)
    return None


def _path_key(path: str) -> str:
    return str(Path(path)).replace("\\", "/").lower()


def _simple_request(client: ObsWebSocketClient, request_type: str, message: str, data: dict[str, Any] | None = None) -> ActionResult:
    result = client.request(request_type, data)
    if not result.ok:
        return _obs_fail(message, result)
    return ActionResult.ok(message)


def _obs_fail(message: str, result: ObsRequestResult) -> ActionResult:
    details = f" {result.comment}" if result.comment else ""
    return ActionResult.fail(f"{message}{details}".strip())
