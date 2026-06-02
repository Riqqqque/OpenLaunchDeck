from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=False)
        file.write("\n")
    os.replace(tmp_path, path)
