from __future__ import annotations

from .run_command import RunCommandAction


class PowerShellAction(RunCommandAction):
    type_name = "powershell"
    display_name = "PowerShell Command"
    description = "Run a PowerShell command."

    def execute(self, context, config: dict):
        command = str(config.get("command") or "").strip()
        if not command:
            return super().execute(context, {"command": "", "wait": True})
        wrapped = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{command}"'
        merged = dict(config)
        merged["command"] = wrapped
        return super().execute(context, merged)
