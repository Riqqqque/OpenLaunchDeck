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


def test_save_replay_buffer_requests_save_when_running():
    client = FakeObsClient(
        [
            ObsRequestResult(True, {"outputActive": True}),
            ObsRequestResult(True, {}),
        ]
    )

    result = run_obs_operation(client, "save_replay_buffer", {"start_if_stopped": True})

    assert result.success is True
    assert result.message == "Replay buffer save requested."
    assert client.requests == [("GetReplayBufferStatus", {}), ("SaveReplayBuffer", {})]
