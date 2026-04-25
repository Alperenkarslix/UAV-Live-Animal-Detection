"""WebSocket endpoint — pushes world-state updates to subscribers."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from uav.db.repository import WorldStateRepository

from .deps import get_bus, get_repo
from .state_bus import StateBus

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws/state")
async def websocket_state(
    ws: WebSocket,
    bus: StateBus = Depends(get_bus),
    repo: WorldStateRepository = Depends(get_repo),
) -> None:
    await ws.accept()
    queue = await bus.subscribe()
    try:
        snapshot = repo.get()
        if snapshot is not None:
            await ws.send_json({"type": "snapshot", "payload": snapshot})

        while True:
            payload = await queue.get()
            await ws.send_json({"type": "update", "payload": payload})
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("websocket /ws/state error")
    finally:
        await bus.unsubscribe(queue)
        with suppress(Exception):
            await ws.close()
