from __future__ import annotations

import base64
import sys
from types import SimpleNamespace

import requests

from openlaunchdeck.actions.base import ActionResult
from openlaunchdeck.actions.delay import DelayAction
from openlaunchdeck.actions.http_request import HttpRequestAction
from openlaunchdeck.actions.noop import NoopAction
from openlaunchdeck.actions.open_path import OpenPathAction
from openlaunchdeck.actions.play_sound import PlaySoundAction
from openlaunchdeck.actions.powershell import PowerShellAction
from openlaunchdeck.actions.run_command import RunCommandAction
from openlaunchdeck.actions.ssh_command import SshCommandAction
from openlaunchdeck.actions.switch_page import SwitchPageAction


def test_noop_and_delay_actions(monkeypatch):
    sleeps = []
    monkeypatch.setattr("openlaunchdeck.actions.delay.time.sleep", sleeps.append)

    assert NoopAction().execute(None, {}).success
    result = DelayAction().execute(None, {"milliseconds": 125})

    assert result.success
    assert sleeps == [0.125]
    assert not DelayAction().execute(None, {"milliseconds": "invalid"}).success


def test_open_path_uses_windows_shell_for_existing_path(tmp_path, monkeypatch):
    opened = []
    target = tmp_path / "item.txt"
    target.write_text("ready", encoding="utf-8")
    monkeypatch.setattr("openlaunchdeck.actions.open_path.sys.platform", "win32")
    monkeypatch.setattr("openlaunchdeck.actions.open_path.os.startfile", opened.append, raising=False)

    result = OpenPathAction().execute(None, {"path": str(target)})

    assert result.success
    assert opened == [str(target)]
    assert not OpenPathAction().execute(None, {"path": str(tmp_path / "missing")}).success


def test_run_command_wait_and_background_paths(monkeypatch):
    run_calls = []
    popen_calls = []

    def fake_run(command, **kwargs):
        kwargs["stdout"].write(b"complete\n")
        run_calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("openlaunchdeck.actions.run_command.subprocess.run", fake_run)
    monkeypatch.setattr(
        "openlaunchdeck.actions.run_command.subprocess.Popen",
        lambda command, **kwargs: popen_calls.append((command, kwargs)),
    )
    monkeypatch.setattr("openlaunchdeck.actions.run_command.sys.platform", "linux")
    action = RunCommandAction()

    waited = action.execute(None, {"command": "status", "wait": True, "timeout": 4})
    started = action.execute(None, {"command": "status", "wait": False})

    assert waited.success and waited.details["output"] == "complete"
    assert run_calls[0][1]["timeout"] == 4
    assert started.success and popen_calls[0][0] == "status"


def test_powershell_encodes_the_command(monkeypatch):
    captured = {}

    def fake_execute(_self, _context, config):
        captured.update(config)
        return ActionResult.ok()

    monkeypatch.setattr(RunCommandAction, "execute", fake_execute)
    result = PowerShellAction().execute(None, {"command": "Write-Output 'ready'", "wait": False})
    encoded = captured["command"].split()[-1]

    assert result.success
    assert base64.b64decode(encoded).decode("utf-16-le") == "Write-Output 'ready'"
    assert "-NoProfile" in captured["command"]


def test_http_request_passes_timeout_and_reports_status(monkeypatch):
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return SimpleNamespace(status_code=204, text="")

    monkeypatch.setattr(requests, "request", fake_request)
    result = HttpRequestAction().execute(
        None,
        {
            "method": "POST",
            "url": "https://example.com/hook",
            "headers": '{"X-Test": "yes"}',
            "body": "payload",
            "timeout": 7,
        },
    )

    assert result.success and result.details["status_code"] == 204
    assert calls == [
        (
            "POST",
            "https://example.com/hook",
            {"headers": {"X-Test": "yes"}, "data": "payload", "timeout": 7.0},
        )
    ]
    assert not HttpRequestAction().execute(None, {"url": "not-a-url"}).success


def test_switch_page_stops_only_page_change_sounds():
    class ProfileService:
        current_page_id = "old"

        def set_current_page(self, page_id):
            self.current_page_id = page_id
            return page_id == "new"

    audio_calls = []
    service = ProfileService()
    context = SimpleNamespace(
        profile_service=service,
        audio_engine=SimpleNamespace(stop_page=lambda *args, **kwargs: audio_calls.append((args, kwargs))),
    )

    result = SwitchPageAction().execute(context, {"page_id": "new"})

    assert result.success and result.details["page_id"] == "new"
    assert audio_calls == [(('old',), {"only_page_change": True})]


def test_play_sound_uses_the_live_page_id(tmp_path):
    sound = tmp_path / "clip.wav"
    sound.write_bytes(b"RIFF")
    calls = []
    context = SimpleNamespace(
        audio_engine=SimpleNamespace(
            play_button_sound=lambda button_id, config: calls.append((button_id, config)) or ActionResult.ok()
        ),
        button_id="A1",
        current_page=SimpleNamespace(id="stale"),
        profile_service=SimpleNamespace(current_page_id="live"),
    )

    result = PlaySoundAction().execute(context, {"file_path": str(sound)})

    assert result.success
    assert calls[0][1]["_page_id"] == "live"


def test_ssh_command_drains_output_and_closes_client(monkeypatch):
    class Channel:
        def __init__(self):
            self.output = [b"remote output"]
            self.error = []

        def recv_ready(self):
            return bool(self.output)

        def recv(self, _size):
            return self.output.pop(0)

        def recv_stderr_ready(self):
            return bool(self.error)

        def recv_stderr(self, _size):
            return self.error.pop(0)

        def exit_status_ready(self):
            return True

        def recv_exit_status(self):
            return 0

        def close(self):
            pass

    class Client:
        def __init__(self):
            self.closed = False
            self.connect_kwargs = None

        def load_system_host_keys(self):
            pass

        def set_missing_host_key_policy(self, _policy):
            pass

        def connect(self, **kwargs):
            self.connect_kwargs = kwargs

        def exec_command(self, _command, timeout):
            assert timeout == 30
            return None, SimpleNamespace(channel=Channel()), None

        def close(self):
            self.closed = True

    client = Client()
    fake_paramiko = SimpleNamespace(SSHClient=lambda: client, RejectPolicy=lambda: object())
    monkeypatch.setitem(sys.modules, "paramiko", fake_paramiko)

    result = SshCommandAction().execute(
        None,
        {"host": "server.example", "port": 22, "username": "user", "command": "status"},
    )

    assert result.success and result.details["output"] == "remote output"
    assert client.connect_kwargs["timeout"] == 10
    assert client.closed is True
