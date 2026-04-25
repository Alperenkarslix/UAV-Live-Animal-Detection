"""Pure-Python geometry helpers used by both API and video processors."""

from __future__ import annotations

import math
from collections.abc import Iterable

EARTH_RADIUS_METRES = 6_371_000.0


def haversine_metres(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Great-circle distance between two (lat, lon) points in metres."""
    lat1, lon1 = map(math.radians, p1)
    lat2, lon2 = map(math.radians, p2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_METRES * c


def polygon_centroid(corners: Iterable[tuple[float, float]]) -> tuple[float, float]:
    """Arithmetic centroid of a closed polygon's vertices.

    Matches the legacy `_build_dataset` calculation (sum / 4 for a 4-corner box).
    """
    pts = list(corners)
    n = len(pts)
    if n == 0:
        raise ValueError("polygon_centroid: no points")
    return sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n


def calculate_pixel_coordinates(
    lat: float,
    lon: float,
    corner_coords: list[tuple[float, float]],
    image_dimensions: tuple[int, int],
) -> tuple[int, int]:
    """Naïve GPS→pixel mapping using axis-aligned bbox of the 4 corners.

    Note: This is the same approximation as the legacy implementation. It does
    not handle rotated/trapezoidal frames correctly — see ROADMAP Faz 2.1 for
    the planned `cv2.getPerspectiveTransform` replacement.
    """
    (lat1, _), (lat2, _), (lat3, _), (lat4, _) = corner_coords[:4]
    (_, lon1), (_, lon2), (_, lon3), (_, lon4) = corner_coords[:4]
    width, height = image_dimensions

    lats = [lat1, lat2, lat3, lat4]
    lons = [lon1, lon2, lon3, lon4]
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)

    if lat_range == 0 or lon_range == 0:
        return width // 2, height // 2

    center_lat = sum(lats) / 4
    center_lon = sum(lons) / 4
    lat_scale = height / lat_range
    lon_scale = width / lon_range

    x = width / 2 + (lon - center_lon) * lon_scale
    y = height / 2 - (lat - center_lat) * lat_scale
    return int(x), int(y)
