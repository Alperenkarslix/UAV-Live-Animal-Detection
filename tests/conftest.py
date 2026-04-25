"""Shared pytest fixtures."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def sample_output_data() -> dict:
    """Minimal output.json shape used across the pipeline."""
    return {
        "center_x": 39.647,
        "center_y": 27.883,
        "animal_coords": {
            "animal_coords_1": {
                "x": 39.6458,
                "y": 27.8796,
                "name": "Hayvan1",
                "temperature": 17.0,
                "distance_metre": 676.66,
            },
        },
        "camera_coords": [
            [39.6454, 27.8807],
            [39.6454, 27.8857],
            [39.6494, 27.8857],
            [39.6494, 27.8807],
        ],
    }
