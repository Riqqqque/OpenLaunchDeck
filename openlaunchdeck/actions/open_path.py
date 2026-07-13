from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .base import ActionResult, BaseAction


class OpenPathAction(BaseAction):
    type_name = "open_path"
    display_name = "Open Path/App"
    description = "Open a file, folder, or application."
    config_fields = [{"name": "path", "label": "Path", "type": "file_or_directory"}]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        raw_path = str(config.get("path") or "").strip().strip('"')
        if not raw_path:
            return ActionResult.fail("Choose a file, folder, or application path.")
        path = Path(os.path.expandvars(raw_path)).expanduser()
        if not path.exists():
            return ActionResult.fail(f"Path does not exist: {path}")
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as exc:
            return ActionResult.fail(f"Could not open path: {exc}")
        return ActionResult.ok(f"Opened {path}.")
