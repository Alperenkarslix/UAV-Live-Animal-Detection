"""Domain-level dataset construction (used by API + simulator)."""

from __future__ import annotations

from typing import Any

from .geo import haversine_metres, polygon_centroid


def build_dataset(
    marker_coords: list[tuple[float, float]],
    rectangle_corners: list[tuple[float, float]],
) -> dict[str, Any]:
    """Construct the canonical output.json shape.

    Mirrors `web_app._build_dataset` so both the legacy Flask app and the new
    FastAPI app produce identical files.
    """
    if len(rectangle_corners) < 4:
        raise ValueError("rectangleData must contain at least 4 corners")

    corners = rectangle_corners[:4]
    center = polygon_centroid(corners)

    animals = {
        f"animal_coords_{i + 1}": {
            "x": coords[0],
            "y": coords[1],
            "name": f"Hayvan{i + 1}",
            "temperature": 15 + (i + 1) * 2,
            "distance_metre": haversine_metres(center, coords),
        }
        for i, coords in enumerate(marker_coords)
    }

    return {
        "center_x": center[0],
        "center_y": center[1],
        "animal_coords": animals,
        "camera_coords": list(corners),
    }
