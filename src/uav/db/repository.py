"""SQLite-backed state repository.

Phase B keeps a single-row JSON snapshot of the world state — same shape as
`output.json`. When we move to PostGIS in Phase E, normalise into
`observations(id, ts, drone_id, lat, lon, ...)` per the ROADMAP.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS world_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL,
    updated_at REAL NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL DEFAULT (strftime('%s','now'))
);
"""


class WorldStateRepository:
    """Thread-safe single-row world-state store."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            self.db_path,
            isolation_level=None,
            check_same_thread=False,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    def get(self) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT payload FROM world_state WHERE id = 1").fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def upsert(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False)
        with self._lock, self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute(
                """
                INSERT INTO world_state (id, payload) VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = strftime('%s','now')
                """,
                (body,),
            )
            conn.execute("INSERT INTO state_history (payload) VALUES (?)", (body,))
            conn.execute("COMMIT")

    def patch_camera(
        self,
        camera_coords: list[list[float]],
        center: tuple[float, float],
    ) -> dict[str, Any]:
        existing = self.get() or {}
        existing.update(
            camera_coords=camera_coords,
            center_x=center[0],
            center_y=center[1],
        )
        self.upsert(existing)
        return existing
