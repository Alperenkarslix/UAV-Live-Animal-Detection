from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from uav.api import app as app_module
from uav.api.deps import _bus, _repo
from uav.core import config as config_module


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("UAV_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("UAV_OUTPUT_JSON", str(tmp_path / "output.json"))

    config_module._settings = None  # type: ignore[attr-defined]
    _repo.cache_clear()
    _bus.cache_clear()

    return TestClient(app_module.create_app())


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_state_404_when_empty(client: TestClient) -> None:
    r = client.get("/api/state")
    assert r.status_code == 404


def test_build_then_get(client: TestClient, tmp_path: Path) -> None:
    r = client.post(
        "/api/state/build",
        data={
            "marker_data": json.dumps([[39.65, 27.88]]),
            "rectangle_data": json.dumps(
                [[39.6454, 27.8807], [39.6454, 27.8857], [39.6494, 27.8857], [39.6494, 27.8807]]
            ),
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "animal_coords_1" in body["animal_coords"]

    output_json = tmp_path / "output.json"
    assert output_json.exists()
    mirrored = json.loads(output_json.read_text())
    assert mirrored["center_x"] == body["center_x"]

    r2 = client.get("/api/state")
    assert r2.status_code == 200
    assert r2.json()["center_x"] == body["center_x"]


def test_legacy_sonuc_alias(client: TestClient) -> None:
    r = client.post(
        "/sonuc",
        data={
            "markerData": json.dumps([[39.65, 27.88]]),
            "rectangleData": json.dumps(
                [[39.6454, 27.8807], [39.6454, 27.8857], [39.6494, 27.8857], [39.6494, 27.8807]]
            ),
        },
    )
    assert r.status_code == 200, r.text


def test_save_camera(client: TestClient) -> None:
    client.post(
        "/api/state/build",
        data={
            "marker_data": json.dumps([[39.65, 27.88]]),
            "rectangle_data": json.dumps(
                [[39.6454, 27.8807], [39.6454, 27.8857], [39.6494, 27.8857], [39.6494, 27.8807]]
            ),
        },
    )
    r = client.post(
        "/api/state/camera",
        json={
            "camera_coords": [[10.0, 20.0]] * 4,
            "center_coords": [15.0, 25.0],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "success"}


def test_websocket_snapshot_then_update(client: TestClient) -> None:
    client.post(
        "/api/state/build",
        data={
            "marker_data": json.dumps([[39.65, 27.88]]),
            "rectangle_data": json.dumps(
                [[39.6454, 27.8807], [39.6454, 27.8857], [39.6494, 27.8857], [39.6494, 27.8807]]
            ),
        },
    )

    with client.websocket_connect("/ws/state") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot"
        assert msg["payload"]["center_x"]
