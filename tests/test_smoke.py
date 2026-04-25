"""Smoke tests — package importable, core invariants hold."""

from __future__ import annotations


def test_package_importable() -> None:
    import uav

    assert uav.__version__


def test_sample_data_shape(sample_output_data: dict) -> None:
    assert len(sample_output_data["camera_coords"]) == 4
    assert sample_output_data["animal_coords"]
