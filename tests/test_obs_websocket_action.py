import os
import time

from openlaunchdeck.actions.base import ActionResult
from openlaunchdeck.actions.obs_websocket import ObsRequestResult, build_obs_auth_response, run_obs_operation


class FakeObsClient:
    def __init__(self, responses, write_screenshots: bool = False):
        self.responses = list(responses)
        self.requests = []
        self.write_screenshots = write_screenshots

    def request(self, request_type, request_data=None):
        self.requests.append((request_type, request_data or {}))
        if self.write_screenshots and request_type == "SaveSourceScreenshot" and request_data:
            screenshot_path = request_data.get("imageFilePath")
            if screenshot_path:
                with open(screenshot_path, "wb") as file:
                    file.write(b"png")
        return self.responses.pop(0)


def test_obs_auth_response_is_stable():
    response = build_obs_auth_response("password", "salt", "challenge")

    assert response == "zTM5ki6L2vVvBQiTG9ckH1Lh64AbnCf6XZ226UmnkIA="


def test_save_replay_buffer_starts_when_stopped():
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"outputActive": False}),
            ObsRequestResult(True, {}),
        ]
    )

    result = run_obs_operation(client, "save_replay_buffer", {"start_if_stopped": True})

    assert isinstance(result, ActionResult)
    assert result.success is True
    assert result.message == "Replay buffer started. Press again to save a clip."
    assert client.requests == [("GetReplayBufferStatus", {}), ("StartReplayBuffer", {})]


def test_save_replay_buffer_requests_save_when_running(tmp_path):
    replay_path = tmp_path / "Replay Test.mp4"
    replay_path.write_bytes(b"mp4")
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"outputActive": True}),
            ObsRequestResult(True, {"savedReplayPath": str(tmp_path / "old.mp4")}),
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"savedReplayPath": str(replay_path)}),
        ]
    )

    result = run_obs_operation(client, "save_replay_buffer", {"start_if_stopped": True})

    assert result.success is True
    assert result.message == "Replay saved: Replay Test.mp4"
    assert result.details["replay_path"] == str(replay_path)
    assert client.requests == [
        ("GetReplayBufferStatus", {}),
        ("GetLastReplayBufferReplay", {}),
        ("SaveReplayBuffer", {}),
        ("GetLastReplayBufferReplay", {}),
    ]


def test_save_replay_buffer_fails_when_no_file_appears(tmp_path):
    missing_path = tmp_path / "missing.mp4"
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"outputActive": True}),
            ObsRequestResult(True, {"savedReplayPath": ""}),
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"savedReplayPath": str(missing_path)}),
        ]
    )

    result = run_obs_operation(client, "save_replay_buffer", {"replay_verify_timeout_ms": 0})

    assert result.success is False
    assert "no replay file appeared" in result.message


def test_save_replay_buffer_waits_past_same_path_with_different_slashes(tmp_path):
    old_path = tmp_path / "old.mp4"
    old_path.write_bytes(b"old")
    old_time = time.time() - 120
    os.utime(old_path, (old_time, old_time))
    replay_path = tmp_path / "new.mp4"
    replay_path.write_bytes(b"new")
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"outputActive": True}),
            ObsRequestResult(True, {"savedReplayPath": old_path.as_posix()}),
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"savedReplayPath": str(old_path)}),
            ObsRequestResult(True, {"savedReplayPath": str(replay_path)}),
        ]
    )

    result = run_obs_operation(client, "save_replay_buffer", {"replay_verify_timeout_ms": 1500})

    assert result.success is True
    assert result.details["replay_path"] == str(replay_path)


def test_save_screenshot_uses_current_scene(tmp_path):
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"currentProgramSceneName": "Scene"}),
            ObsRequestResult(True, {}),
        ],
        write_screenshots=True,
    )

    result = run_obs_operation(
        client,
        "save_screenshot",
        {"screenshot_folder": str(tmp_path), "screenshot_format": "png"},
    )

    assert result.success is True
    assert result.details["screenshot_path"].endswith(".png")
    assert client.requests[0] == ("GetCurrentProgramScene", {})
    request_type, request_data = client.requests[1]
    assert request_type == "SaveSourceScreenshot"
    assert request_data["sourceName"] == "Scene"
    assert request_data["imageFormat"] == "png"
    assert str(tmp_path) in request_data["imageFilePath"]


def test_save_screenshot_defaults_to_obs_record_directory(tmp_path):
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"currentProgramSceneName": "Scene"}),
            ObsRequestResult(True, {"recordDirectory": str(tmp_path)}),
            ObsRequestResult(True, {}),
        ],
        write_screenshots=True,
    )

    result = run_obs_operation(client, "save_screenshot", {"screenshot_format": "png"})

    assert result.success is True
    assert result.details["screenshot_path"].startswith(str(tmp_path))
    assert client.requests[1] == ("GetRecordDirectory", {})


def test_hide_source_sets_and_verifies_scene_item_visibility():
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"sceneItemId": 4}),
            ObsRequestResult(True, {"sceneItemEnabled": True}),
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"sceneItemEnabled": False}),
        ]
    )

    result = run_obs_operation(client, "hide_source", {"scene_name": "Scene", "source_name": "Camera"})

    assert result.success is True
    assert result.message == "Camera hidden."
    assert client.requests == [
        ("GetSceneItemId", {"sceneName": "Scene", "sourceName": "Camera", "searchOffset": 0}),
        ("GetSceneItemEnabled", {"sceneName": "Scene", "sceneItemId": 4}),
        ("SetSceneItemEnabled", {"sceneName": "Scene", "sceneItemId": 4, "sceneItemEnabled": False}),
        ("GetSceneItemEnabled", {"sceneName": "Scene", "sceneItemId": 4}),
    ]


def test_toggle_source_uses_current_scene_when_scene_name_is_blank():
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"currentProgramSceneName": "Scene"}),
            ObsRequestResult(True, {"sceneItemId": 4}),
            ObsRequestResult(True, {"sceneItemEnabled": False}),
            ObsRequestResult(True, {"sceneItemId": 4}),
            ObsRequestResult(True, {"sceneItemEnabled": False}),
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"sceneItemEnabled": True}),
        ]
    )

    result = run_obs_operation(client, "toggle_source", {"source_name": "Camera"})

    assert result.success is True
    assert result.message == "Camera shown."
    assert client.requests[0] == ("GetCurrentProgramScene", {})
    assert client.requests[-1] == ("GetSceneItemEnabled", {"sceneName": "Scene", "sceneItemId": 4})


def test_set_input_mute_verifies_obs_state():
    client = FakeObsClient(
        [
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"inputMuted": True}),
        ]
    )

    result = run_obs_operation(client, "mute_input", {"input_name": "Mic/Aux"})

    assert result.success is True
    assert result.message == "Mic/Aux muted."
    assert client.requests == [
        ("SetInputMute", {"inputName": "Mic/Aux", "inputMuted": True}),
        ("GetInputMute", {"inputName": "Mic/Aux"}),
    ]


def test_set_input_mute_fails_if_verification_disagrees():
    client = FakeObsClient(
        [
            ObsRequestResult(True, {}),
            ObsRequestResult(True, {"inputMuted": False}),
        ]
    )

    result = run_obs_operation(client, "mute_input", {"input_name": "Mic/Aux"})

    assert result.success is False
    assert "did not verify" in result.message
