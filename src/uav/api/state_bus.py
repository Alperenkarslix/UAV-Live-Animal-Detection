"""In-memory pub/sub for fan-out to WebSocket clients.

Replaces polling. When a route mutates state, it `publish()`es; every
`/ws/state` consumer receives the new payload. No external broker needed
for single-process dev — Redis pub/sub fits in here when we scale.
"""

from __future__ import annotations

import asyncio
from typing import Any


class StateBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=16)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            stale = []
            for q in self._subscribers:
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    stale.append(q)
            for q in stale:
                self._subscribers.discard(q)
