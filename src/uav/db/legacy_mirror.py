"""Mirror state changes back to `output.json` for the legacy video processors.

`videoproc_video.py` / `videoproc_realtime.py` read `output.json` via mtime
polling. While both old + new code paths coexist, every API mutation writes
both targets atomically.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(payload: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    directory = path.parent if path.parent != Path("") else Path(".")
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".output_", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
