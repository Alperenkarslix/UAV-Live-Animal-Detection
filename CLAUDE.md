# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick start

```bash
# Backend (Python)
uv sync --extra dev --extra ml         # creates .venv, installs FastAPI + Ultralytics + dev tools
just check                              # ruff lint + format check + pytest
just dev                                # FastAPI on http://127.0.0.1:8000

# Frontend (Node)
cd web && npm install && npm run build  # production bundle to web/dist
cd web && npm run dev                   # Vite dev server on http://localhost:5173 (proxies /api + /ws)

# Legacy pipeline (still works)
just video                              # videoproc_video.py — overlay + YOLO on testvideo.mp4
just realtime                           # videoproc_realtime.py — webcam
just simulate                           # simulate_movement.py — random GPS jitter
```

In any OpenCV window: `y` toggles YOLO inference, `q` quits.

All Python runtime parameters are env vars handled by `pydantic-settings` (`src/uav/core/config.py`):
`UAV_MODEL`, `UAV_CONF`, `UAV_IMGSZ`, `UAV_TRACKER`, `UAV_DEVICE`, `UAV_STRIDE`, `UAV_VIDEO`, `UAV_CAM`,
`UAV_API_HOST`, `UAV_API_PORT`, `UAV_DB_PATH`, `UAV_OUTPUT_JSON`, `UAV_LOG_LEVEL`. Copy `.envrc.example`
to `.envrc` and `direnv allow` to load defaults on `cd`.

Apple Silicon: prefer CoreML (`uv run python scripts/export_coreml.py` then `UAV_MODEL=…/best.mlpackage`)
over PyTorch MPS — Neural Engine is more deterministic. Benchmark with `uv run python scripts/benchmark.py`.

## Architecture

The project is mid-migration from a Flask + JSON-file prototype to a FastAPI + SQLite + React stack.
**Both stacks coexist and share the same data shape** so the legacy video processors keep working.

### Data flow (current)

```
React UI (web/)                        videoproc_*.py (legacy CV loop)
   │                                          │
   │ POST /api/state/build                    │ reads (mtime polling)
   ▼                                          ▼
FastAPI (src/uav/api)  ──atomic write──►  output.json
   │                                          ▲
   │ upsert/get                               │ atomic write
   ▼                                          │
SQLite (uav.db, world_state row)              │
   │                                          │
   └──────────►  StateBus (asyncio)  ─────►  WS /ws/state ──► React live state
                                              │
                                              │ POST /sonuc (legacy alias)
                                              │
                                  templates/index.html (Yandex, optional)
```

`output.json` is the **legacy compatibility mirror** — every API mutation writes both SQLite and the
JSON file via `db/legacy_mirror.atomic_write_json` (using `tempfile.mkstemp` + `os.replace`). The video
processors have not been touched in this migration; they continue to read `output.json` through
`video_common.CachedJson` and only reload when mtime changes.

### Source layout

```
src/uav/
  core/
    config.py          # pydantic-settings — single source of truth for all UAV_* env vars
    geo.py             # haversine_metres, polygon_centroid, calculate_pixel_coordinates
    dataset.py         # build_dataset() — same shape as legacy _build_dataset
  db/
    repository.py      # WorldStateRepository — sqlite3 with WAL, single-row world_state table
    legacy_mirror.py   # atomic_write_json for output.json compat
  api/
    app.py             # FastAPI factory + lifespan (seeds SQLite from output.json on first boot)
    routes.py          # /api/state, /api/state/build, /api/state/camera + legacy aliases /sonuc, /get_data, /save_coordinates
    websocket.py       # /ws/state — pushes snapshot then updates
    state_bus.py       # in-memory asyncio pub/sub (replace with Redis when scaling)
    schemas.py         # Pydantic request/response models
    deps.py            # FastAPI Depends() wiring (lru_cache singletons)
  inference/           # (placeholder — see scripts/ for export + benchmark)
  cli/                 # (placeholder — videoproc_*.py still live at repo root)

scripts/
  export_coreml.py     # Ultralytics → .mlpackage for Apple Neural Engine
  benchmark.py         # mean/p50/p95/p99 ms/frame + FPS

web/                   # Vite + React 19 + TypeScript + Tailwind v4 + MapLibre GL JS
  src/App.tsx          # mode switcher (add-animal / edit-camera / view) + WebSocket sync
  src/components/MapView.tsx   # MapLibre map, draggable markers, GeoJSON polygon for camera FOV
  src/components/Sidebar.tsx
  src/api.ts           # fetchState, buildState, saveCamera, streamState (auto-reconnect WS)
  vite.config.ts       # proxies /api, /healthz, /ws to UAV_API_URL (default http://127.0.0.1:8000)

tests/                 # pytest — geo, repository, api (with WebSocket smoke), smoke
```

### Legacy files at repo root (not migrated)

`config.py`, `video_common.py`, `videoproc_video.py`, `videoproc_realtime.py`, `simulate_movement.py`,
`web_app.py`, `yolo_test_*.py`, `templates/`. These still work but are scheduled to move into
`src/uav/cli/` and `src/uav/inference/`. Do not break the public behaviour of `output.json` when
editing — the video processors depend on it.

### Non-obvious points

- **The default model is the fine-tuned `yolomodel/yolo26_animals/weights/best.pt`**, not COCO.
  `yolomodel/` is now gitignored; the repo no longer ships weights — distribute via Releases / S3 /
  Hugging Face Hub. `yolo26n.pt` / `yolo26s.pt` at repo root are COCO baselines kept for comparison
  via `UAV_MODEL=`.
- **Two virtualenvs may exist on disk.** `env/` is the legacy `python -m venv` install; `.venv/` is
  the new `uv sync` install. Always use `uv run …` or activate `.venv/bin/activate` for new work.
- **`calculate_pixel_coordinates` is still a naïve bbox mapping**, not a homography. Trapezoidal /
  rotated frames are wrong. The replacement (`cv2.getPerspectiveTransform`) is ROADMAP Faz 2.1.
- **YOLO toggle preserves previous detections.** When `UAV_STRIDE > 1`, processors draw
  `cached_detections` from the last inferred frame on intermediate frames — boxes appear to lag,
  this is intentional.
- **Model training is not wired into any entry point.** `yolo_train.ipynb` is meant for
  Kaggle/Colab; the produced zip is unpacked into `yolomodel/` locally.
- **Code mixes Turkish and English.** README, comments, and some identifiers (`hesapla_metre`,
  `EDGE_NAMES = ["Sag Taraf", ...]`) are Turkish. Match the surrounding language when editing.
- **Tests cover the new package.** `tests/` exercises `core/`, `db/`, `api/` with `pytest --cov`
  enforced (currently ~88%). Legacy root-level scripts have no tests.

## Roadmap context

`ROADMAP.md` lays out phases 0–8. Phase 0 (foundation hardening) and most of Phase 1 (object
tracking via ByteTrack, fine-tuned model) are done. The current refactor delivers chunks of
Phase 3.2 (FastAPI + WebSocket + MapLibre) and prepares for Phase 4.1 (PostgreSQL + PostGIS) by
gating all writes through a repository abstraction. When extending the project, check the roadmap
before inventing a design — the homography rewrite, live RTSP intake, and PostGIS migration are
already scoped there.
