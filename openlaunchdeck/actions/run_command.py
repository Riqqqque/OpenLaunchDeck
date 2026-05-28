from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ..constants import DEFAULT_COMMAND_TIMEOUT_SECONDS
from .base import ActionResult, BaseAction


class RunCommandAction(BaseAction):
    type_name = "run_command"
    display_name = "Run Command"
    description = "Run a local command."
    config_fields = [
        {"name": "command", "label": "Command", "type": "text"},
        {"name": "working_directory", "label": "Working Directory", "type": "path"},
        {"name": "run_hidden", "label": "Run Hidden", "type": "bool"},
        {"name": "wait", "label": "Wait For Completion", "type": "bool"},
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        command = str(config.get("command") or "").strip()
        if not command:
            return ActionResult.fail("Command is empty.")
        cwd = str(config.get("working_directory") or "").strip() or None
        if cwd and not Path(cwd).exists():
            return ActionResult.fail(f"Working directory does not exist: {cwd}")
        hidden = bool(config.get("run_hidden", True))
        wait = bool(config.get("wait", False))
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32" and hidden:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW
        try:
            if wait:
                completed = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    timeout=int(config.get("timeout", DEFAULT_COMMAND_TIMEOUT_SECONDS)),
                    capture_output=True,
                    text=True,
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
                if completed.returncode != 0:
                    detail = (completed.stderr or completed.stdout or "").strip()
                    return ActionResult.fail(f"Command failed with exit code {completed.returncode}.", output=detail)
                return ActionResult.ok("Command completed.", output=(completed.stdout or "").strip())
            subprocess.Popen(command, shell=True, cwd=cwd, startupinfo=startupinfo, creationflags=creationflags)
            return ActionResult.ok("Command started.")
        except Exception as exc:
            return ActionResult.fail(f"Command could not run: {exc}")
