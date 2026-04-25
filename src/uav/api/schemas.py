"""Pydantic request/response models."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

LatLon = Annotated[
    tuple[float, float],
    Field(description="(latitude, longitude) pair in WGS84 decimal degrees"),
]


class AnimalCoord(BaseModel):
    model_config = ConfigDict(extra="allow")

    x: float
    y: float
    name: str
    temperature: float
    distance_metre: float


class WorldState(BaseModel):
    """Canonical shape of `output.json`."""

    center_x: float
    center_y: float
    animal_coords: dict[str, AnimalCoord] = Field(default_factory=dict)
    camera_coords: list[list[float]] = Field(default_factory=list)


class BuildDatasetRequest(BaseModel):
    marker_data: list[LatLon] = Field(min_length=1)
    rectangle_data: list[LatLon] = Field(min_length=4)


class SaveCoordinatesRequest(BaseModel):
    camera_coords: list[list[float]] = Field(min_length=4)
    center_coords: LatLon


class StatusResponse(BaseModel):
    status: str
