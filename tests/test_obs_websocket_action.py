import os
import time

from openlaunchdeck.actions.base import ActionResult
from openlaunchdeck.actions.obs_websocket import ObsRequestResult, build_obs_auth_response, run_obs_operation


class FakeObsClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def request(self, request_type, request_data=None):
        self.requests.append((request_type, request_data or {}))
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
        ]
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
