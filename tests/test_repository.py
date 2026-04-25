from __future__ import annotations

from pathlib import Path

import pytest

from uav.db.repository import WorldStateRepository


@pytest.fixture
def repo(tmp_path: Path) -> WorldStateRepository:
    return WorldStateRepository(tmp_path / "test.db")


def test_get_returns_none_when_empty(repo: WorldStateRepository) -> None:
    assert repo.get() is None


def test_upsert_roundtrip(repo: WorldStateRepository, sample_output_data: dict) -> None:
    repo.upsert(sample_output_data)
    fetched = repo.get()
    assert fetched is not None
    assert fetched["center_x"] == sample_output_data["center_x"]
    assert fetched["animal_coords"]["animal_coords_1"]["name"] == "Hayvan1"


def test_upsert_overwrites_single_row(repo: WorldStateRepository) -> None:
    repo.upsert({"center_x": 1.0, "center_y": 2.0, "animal_coords": {}, "camera_coords": []})
    repo.upsert({"center_x": 9.0, "center_y": 8.0, "animal_coords": {}, "camera_coords": []})
    state = repo.get()
    assert state is not None
    assert state["center_x"] == 9.0


def test_patch_camera(repo: WorldStateRepository, sample_output_data: dict) -> None:
    repo.upsert(sample_output_data)
    repo.patch_camera(
        camera_coords=[[10.0, 20.0]] * 4,
        center=(15.0, 25.0),
    )
    state = repo.get()
    assert state is not None
    assert state["center_x"] == 15.0
    assert state["camera_coords"][0] == [10.0, 20.0]
    # animal_coords preserved from prior upsert
    assert "animal_coords_1" in state["animal_coords"]
