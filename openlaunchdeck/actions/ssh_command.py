from __future__ import annotations

from .base import ActionResult, BaseAction


class SshCommandAction(BaseAction):
    type_name = "ssh_command"
    display_name = "SSH Command"
    description = "Run a command over SSH using key-based auth."
    config_fields = [
        {"name": "host", "label": "Host", "type": "text"},
        {"name": "port", "label": "Port", "type": "number"},
        {"name": "username", "label": "Username", "type": "text"},
        {"name": "key_filename", "label": "Private Key", "type": "file"},
        {"name": "command", "label": "Command", "type": "text"},
    ]
    blocking = True

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
            _, stdout, stderr = client.exec_command(command, timeout=30)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode(errors="replace")
            error = stderr.read().decode(errors="replace")
        except Exception as exc:
            return ActionResult.fail(f"SSH command failed: {exc}")
        finally:
            client.close()
        if exit_status != 0:
            return ActionResult.fail(f"SSH command exited with {exit_status}.", output=error[:1000])
        return ActionResult.ok("SSH command completed.", output=output[:1000])
