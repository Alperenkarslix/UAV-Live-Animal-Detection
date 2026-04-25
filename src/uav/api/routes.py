"""HTTP routes — replaces the legacy Flask endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Form, HTTPException, status

from uav.core.config import Settings
from uav.core.dataset import build_dataset
from uav.db.legacy_mirror import atomic_write_json
from uav.db.repository import WorldStateRepository

from .deps import get_bus, get_repo, settings_dep
from .schemas import SaveCoordinatesRequest, StatusResponse, WorldState
from .state_bus import StateBus

router = APIRouter()


@router.get("/healthz", response_model=StatusResponse, tags=["meta"])
async def healthz() -> StatusResponse:
    return StatusResponse(status="ok")


@router.get("/api/state", response_model=WorldState, tags=["state"])
async def get_state(repo: WorldStateRepository = Depends(get_repo)) -> WorldState:
    data = repo.get()
    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="no state yet")
    return WorldState.model_validate(data)


@router.post("/api/state/build", response_model=WorldState, tags=["state"])
async def post_build_dataset(
    marker_data: str = Form(...),
    rectangle_data: str = Form(...),
    repo: WorldStateRepository = Depends(get_repo),
    bus: StateBus = Depends(get_bus),
    settings: Settings = Depends(settings_dep),
) -> WorldState:
    """Mirror of legacy `POST /sonuc`.

    Accepts the same form-encoded JSON strings the Flask UI sends so the
    existing `templates/index.html` keeps working unchanged.
    """
    try:
        markers = json.loads(marker_data)
        rectangle = json.loads(rectangle_data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not isinstance(markers, list) or not isinstance(rectangle, list):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid data shape")
    if not markers or len(rectangle) < 4:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="missing data")

    payload = build_dataset(markers, rectangle)
    repo.upsert(payload)
    atomic_write_json(payload, settings.absolute_output_json)
    await bus.publish(payload)
    return WorldState.model_validate(payload)


@router.post("/api/state/camera", response_model=StatusResponse, tags=["state"])
async def post_save_camera(
    body: SaveCoordinatesRequest,
    repo: WorldStateRepository = Depends(get_repo),
    bus: StateBus = Depends(get_bus),
    settings: Settings = Depends(settings_dep),
) -> StatusResponse:
    payload = repo.patch_camera(body.camera_coords, body.center_coords)
    atomic_write_json(payload, settings.absolute_output_json)
    await bus.publish(payload)
    return StatusResponse(status="success")


# --- Legacy compatibility (matches Flask route names) -----------------------


@router.post("/sonuc", include_in_schema=False)
async def legacy_sonuc(
    marker_data: str = Form(..., alias="markerData"),
    rectangle_data: str = Form(..., alias="rectangleData"),
    repo: WorldStateRepository = Depends(get_repo),
    bus: StateBus = Depends(get_bus),
    settings: Settings = Depends(settings_dep),
) -> WorldState:
    return await post_build_dataset(marker_data, rectangle_data, repo, bus, settings)


@router.get("/get_data", include_in_schema=False)
async def legacy_get_data(repo: WorldStateRepository = Depends(get_repo)) -> WorldState:
    return await get_state(repo)


@router.post("/save_coordinates", include_in_schema=False)
async def legacy_save_coordinates(
    body: SaveCoordinatesRequest,
    repo: WorldStateRepository = Depends(get_repo),
    bus: StateBus = Depends(get_bus),
    settings: Settings = Depends(settings_dep),
) -> StatusResponse:
    return await post_save_camera(body, repo, bus, settings)
