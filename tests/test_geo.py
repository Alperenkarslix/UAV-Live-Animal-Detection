from __future__ import annotations

import math

from uav.core.dataset import build_dataset
from uav.core.geo import calculate_pixel_coordinates, haversine_metres, polygon_centroid


def test_haversine_zero_distance() -> None:
    assert haversine_metres((39.0, 27.0), (39.0, 27.0)) == 0.0


def test_haversine_one_degree_lat_is_about_111km() -> None:
    d = haversine_metres((39.0, 27.0), (40.0, 27.0))
    assert math.isclose(d, 111_195, rel_tol=0.01)


def test_polygon_centroid_square() -> None:
    cx, cy = polygon_centroid([(0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0)])
    assert (cx, cy) == (1.0, 1.0)


def test_calculate_pixel_centred() -> None:
    corners = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
    px, py = calculate_pixel_coordinates(0.5, 0.5, corners, (640, 480))
    assert (px, py) == (320, 240)


def test_calculate_pixel_degenerate_corners() -> None:
    corners = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
    px, py = calculate_pixel_coordinates(0.5, 0.5, corners, (640, 480))
    assert (px, py) == (320, 240)


def test_build_dataset_shape() -> None:
    payload = build_dataset(
        marker_coords=[(39.65, 27.88)],
        rectangle_corners=[
            (39.6454, 27.8807),
            (39.6454, 27.8857),
            (39.6494, 27.8857),
            (39.6494, 27.8807),
        ],
    )
    assert "center_x" in payload
    assert "center_y" in payload
    assert len(payload["camera_coords"]) == 4
    assert "animal_coords_1" in payload["animal_coords"]
    assert payload["animal_coords"]["animal_coords_1"]["distance_metre"] > 0
