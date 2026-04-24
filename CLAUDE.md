# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Setup (once):
```bash
python3 -m venv env && source env/bin/activate
pip install -r requirements.txt
```

Run the pipeline (these are the common commands — no build/lint/test suite is configured):
```bash
python web_app.py              # Flask on :5000 → writes output.json from map UI
python simulate_movement.py    # Randomly nudges animal coords in output.json (loop)
python videoproc_video.py      # Overlay + YOLO on videos/testvideo.mp4
python videoproc_realtime.py   # Overlay + YOLO on webcam
python yolo_test_video.py      # Bare YOLO detector on a video (no overlay)
python yolo_test_realtime.py   # Bare YOLO detector on webcam
```

In the OpenCV window: `y` toggles YOLO inference on/off, `q` quits.

All runtime parameters are environment variables read in `config.py`. Override without editing code:
```bash
UAV_DEVICE=mps python videoproc_realtime.py          # Apple Silicon
UAV_CONF=0.3 UAV_IMGSZ=960 python videoproc_video.py # small/distant animals
UAV_VIDEO=videos/safari.mp4 UAV_STRIDE=3 python videoproc_video.py
UAV_MODEL=yolo26s.pt python videoproc_video.py       # COCO baseline (weak on safari classes)
```
Full list: `UAV_MODEL`, `UAV_CONF`, `UAV_IMGSZ`, `UAV_TRACKER`, `UAV_DEVICE`, `UAV_STRIDE`, `UAV_VIDEO`, `UAV_CAM`.

## Architecture

This is a **two-process pipeline coupled by `output.json`**. Understanding this file is the whole architecture:

1. **`web_app.py`** (Flask + Yandex Maps) is the **writer**. The user places animal markers and a 4-corner camera polygon on a map; `POST /sonuc` calls `_build_dataset` to compute per-animal Haversine distance from the polygon center, then does an **atomic write** (`_atomic_write_json` via `tempfile.mkstemp` + `os.replace`, guarded by `_file_lock`) to `output.json`.

2. **`videoproc_video.py` / `videoproc_realtime.py`** are the **readers**. They poll `output.json` through `video_common.CachedJson`, which reloads only when the file's mtime changes. For every frame they call `render_overlay` to draw the overlay, then (when YOLO is toggled on) `detect_yolo` + `draw_detections`.

3. **`video_common.py`** is the shared core — both processors import from it. Key functions:
   - `calculate_pixel_coordinates(lat, lon, corner_coords, image_dims)` — naïve GPS→pixel mapping using the axis-aligned bounding box of the 4 corners (NOT a homography; trapezoid/rotated frames will be wrong — see ROADMAP Faz 2.1 for planned `cv2.getPerspectiveTransform` replacement).
   - `render_overlay` — uses `shapely.Polygon.contains` to split animals into **inside camera FOV** (blue box + temperature) vs **outside FOV** (arrow pointing to nearest polygon edge + distance in metres + Turkish edge name from `EDGE_NAMES`).
   - `auto_orient(frame)` — portrait frames (`h > w`) get rotated 90° clockwise. This also flips the capture dimensions (`width, height = height, width`) when building `corner_points`.
   - `detect_yolo(..., use_tracking=True)` — uses `model.track(persist=True, tracker='bytetrack.yaml')` for stable IDs; returned tuples include `track_id`.
   - `load_yolo` imports `ultralytics` lazily so non-YOLO entry points (like `web_app.py`) don't pay the import cost.

4. **`simulate_movement.py`** is an optional third process used when there is no live UAV feed. It mutates `output.json`'s `animal_coords` with small random GPS offsets every 5 s and recomputes `distance_metre`. Like `web_app.py`, it uses atomic writes.

### Non-obvious points

- **Default model is fine-tuned, not COCO.** `config.MODEL_PATH` defaults to `yolomodel/yolo26_animals/weights/best.pt` (6 safari classes: Elephant, Giraffe, Impala, Lechwe, Tsessebe, Zebra, mAP50 ≈ 0.911). `yolo26n.pt` / `yolo26s.pt` in the repo root are **COCO baselines** and will detect far fewer animals — only swap them in via `UAV_MODEL=` for comparison runs.
- **`output.json` is live shared state, not a fixture.** Don't pin tests or features to its current contents; it gets rewritten by the Flask UI and the movement simulator.
- **YOLO toggle preserves previous detections.** When `UAV_STRIDE > 1`, the processors draw `cached_detections` from the last inferred frame on every intermediate frame — boxes appear to lag, this is intentional frame-skipping.
- **Model training happens outside the repo.** `yolo_train.ipynb` is meant for Kaggle/Colab (2× T4, ~1 hr). The output zip is unpacked into `yolomodel/` locally — training code is not wired into any Python entry point.
- **README and code comments are in Turkish.** Variable/function names mix Turkish (`hesapla_kus`, `hesapla_metre`, `EDGE_NAMES = ["Sag Taraf", ...]`) and English. Match the surrounding language when editing.
- **No test/lint tooling is configured.** `ROADMAP.md` mentions a "12/12 smoke test" but there is no `tests/` directory — don't claim test coverage that doesn't exist.

## Roadmap context

`ROADMAP.md` lays out phases 0–8. Phase 0 is complete. When extending the project, check the roadmap before inventing a design — for example, the pixel-mapping rewrite (homography), WebSocket live video, and PostGIS migration are all already scoped there.
