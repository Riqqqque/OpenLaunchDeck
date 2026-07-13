from __future__ import annotations

import base64

from .run_command import RunCommandAction


class PowerShellAction(RunCommandAction):
    type_name = "powershell"
    display_name = "PowerShell Command"
    description = "Run a PowerShell command."

    def execute(self, context, config: dict):
        command = str(config.get("command") or "").strip()
        if not command:
            return super().execute(context, {"command": "", "wait": True})
        encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
        wrapped = f"powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand {encoded}"
        merged = dict(config)
        merged["command"] = wrapped
        return super().execute(context, merged)
