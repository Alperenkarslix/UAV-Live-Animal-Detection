"""FastAPI application factory."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from uav.core.config import Settings, get_settings

from .deps import get_repo
from .routes import router
from .websocket import ws_router

logger = logging.getLogger(__name__)


def _bootstrap_state_from_json(settings: Settings) -> None:
    """If `output.json` exists but the DB is empty, seed it once.

    Keeps the new API compatible with state created by the old Flask app.
    """
    repo = get_repo()
    if repo.get() is not None:
        return
    json_path = settings.absolute_output_json
    if not json_path.exists():
        return
    try:
        payload = json.loads(json_path.read_text())
        repo.upsert(payload)
        logger.info("Seeded SQLite state from %s", json_path)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not seed state from %s: %s", json_path, exc)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _bootstrap_state_from_json(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="UAV Live Animal Detection API",
        version="0.2.0",
        lifespan=_lifespan,
    )

    # Wide-open CORS while frontend runs on a different port (Vite :5173).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    repo_root = settings.repo_root
    templates_dir = repo_root / "templates"
    if templates_dir.is_dir():
        templates = Jinja2Templates(directory=str(templates_dir))

        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def index(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(request, "index.html")

    static_dir = repo_root / "web" / "dist"
    if static_dir.is_dir():
        app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="frontend")

    app.include_router(router)
    app.include_router(ws_router)
    return app


app = create_app()


def run() -> None:
    """Entrypoint for `uvicorn uav.api.app:run`."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "uav.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
