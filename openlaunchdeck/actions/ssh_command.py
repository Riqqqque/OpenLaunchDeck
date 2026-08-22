from __future__ import annotations

import time

from .base import ActionResult, BaseAction


MAX_SSH_OUTPUT_BYTES = 64 * 1024


class SshCommandAction(BaseAction):
    type_name = "ssh_command"
    display_name = "SSH Command"
    description = "Run a remote command using SSH keys and known-host verification. Passwords are not stored."
    config_fields = [
        {"name": "host", "label": "Host", "type": "text", "placeholder": "Server hostname or IP address"},
        {"name": "port", "label": "Port", "type": "number", "min": 1, "max": 65535, "default": 22},
        {"name": "username", "label": "Username", "type": "text"},
        {"name": "key_filename", "label": "Private Key", "type": "file"},
        {"name": "command", "label": "Command", "type": "text", "placeholder": "Remote command to run"},
    ]
    blocking = True

    def validate(self, config: dict) -> list[str]:
        if not str(config.get("host") or "").strip():
            return ["Enter an SSH host."]
        if not str(config.get("username") or "").strip():
            return ["Enter an SSH username."]
        if not str(config.get("command") or "").strip():
            return ["Enter a remote command."]
        try:
            port = int(config.get("port") or 22)
        except (TypeError, ValueError):
            return ["SSH port must be a whole number."]
        return [] if 1 <= port <= 65535 else ["SSH port must be between 1 and 65535."]

    def execute(self, context, config: dict) -> ActionResult:
        try:
            import paramiko
        except Exception:
            return ActionResult.fail("SSH dependency is not installed.")
        host = str(config.get("host") or "").strip()
        username = str(config.get("username") or "").strip()
        command = str(config.get("command") or "").strip()
        key_filename = str(config.get("key_filename") or "").strip() or None
        if not host or not username or not command:
            return ActionResult.fail("SSH host, username, and command are required.")
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            client.connect(
                hostname=host,
                port=int(config.get("port") or 22),
                username=username,
                key_filename=key_filename,
                timeout=10,
                auth_timeout=10,
                look_for_keys=True,
            )
            _, stdout, _stderr = client.exec_command(command, timeout=30)
            exit_status, output_bytes, error_bytes = _drain_channel(stdout.channel, timeout=30)
            output = output_bytes.decode(errors="replace")
            error = error_bytes.decode(errors="replace")
        except Exception as exc:
            return ActionResult.fail(f"SSH command failed: {exc}")
        finally:
            client.close()
        if exit_status != 0:
            return ActionResult.fail(f"SSH command exited with {exit_status}.", output=error[:1000])
        return ActionResult.ok("SSH command completed.", output=output[:1000])


def _drain_channel(channel, timeout: float) -> tuple[int, bytes, bytes]:
    deadline = time.monotonic() + max(0.1, timeout)
    output = bytearray()
    error = bytearray()
    while True:
        had_data = False
        while channel.recv_ready():
            chunk = channel.recv(4096)
            if not chunk:
                break
            _append_bounded(output, chunk)
            had_data = True
        while channel.recv_stderr_ready():
            chunk = channel.recv_stderr(4096)
            if not chunk:
                break
            _append_bounded(error, chunk)
            had_data = True
        if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
            return channel.recv_exit_status(), bytes(output), bytes(error)
        if time.monotonic() >= deadline:
            channel.close()
            raise TimeoutError(f"SSH command timed out after {timeout:g} seconds.")
        if not had_data:
            time.sleep(0.01)


def _append_bounded(buffer: bytearray, chunk: bytes) -> None:
    remaining = MAX_SSH_OUTPUT_BYTES - len(buffer)
    if remaining > 0:
        buffer.extend(chunk[:remaining])
