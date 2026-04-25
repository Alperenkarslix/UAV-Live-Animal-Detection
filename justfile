# UAV Live Animal Detection — task runner
# Install: brew install just direnv
# List recipes: `just` or `just --list`

set dotenv-load := true
set positional-arguments := true

PYTHON := "uv run"

# Default: list recipes
default:
    @just --list

# --- Setup -------------------------------------------------------------------

# Create .venv and install all extras (dev + ml)
install:
    uv sync --extra dev --extra ml

# Install legacy Flask app extras too (transitional)
install-all:
    uv sync --extra dev --extra ml --extra legacy

# Refresh lock from pyproject.toml
lock:
    uv lock

# --- Code quality -------------------------------------------------------------

# Run ruff lint
lint:
    {{PYTHON}} ruff check .

# Auto-fix lint issues + format
fix:
    {{PYTHON}} ruff check --fix .
    {{PYTHON}} ruff format .

# Format only
fmt:
    {{PYTHON}} ruff format .

# Run all tests
test *args="":
    {{PYTHON}} pytest {{args}}

# Fast tests (skip slow + yolo + integration)
test-fast:
    {{PYTHON}} pytest -m "not slow and not yolo and not integration"

# Pre-flight: lint + format check + tests
check:
    {{PYTHON}} ruff check .
    {{PYTHON}} ruff format --check .
    {{PYTHON}} pytest -q

# --- Run the pipeline ---------------------------------------------------------

# FastAPI dev server (autoreload)
dev:
    {{PYTHON}} uvicorn uav.api.app:app --reload --host 127.0.0.1 --port 8000

# Legacy Flask app (will be retired)
dev-legacy:
    {{PYTHON}} python web_app.py

# Video file overlay + YOLO
video *args="":
    {{PYTHON}} python videoproc_video.py {{args}}

# Webcam realtime overlay + YOLO
realtime *args="":
    {{PYTHON}} python videoproc_realtime.py {{args}}

# Move animal coordinates randomly (no live UAV)
simulate:
    {{PYTHON}} python simulate_movement.py

# --- Inference / models -------------------------------------------------------

# Export fine-tuned PyTorch weights to CoreML (Apple Neural Engine)
export-coreml model="yolomodel/yolo26_animals/weights/best.pt":
    {{PYTHON}} python scripts/export_coreml.py {{model}}

# Benchmark inference on a video (FPS + ms/frame)
benchmark video="videos/testvideo.mp4":
    {{PYTHON}} python scripts/benchmark.py {{video}}

# --- Frontend (Faz D) ---------------------------------------------------------

# Install Node deps
web-install:
    cd web && npm install

# Vite dev server
web-dev:
    cd web && npm run dev

# Build production bundle
web-build:
    cd web && npm run build

# --- Housekeeping -------------------------------------------------------------

# Remove caches and build artefacts
clean:
    rm -rf .pytest_cache .ruff_cache .coverage coverage.xml
    find . -type d -name __pycache__ -prune -exec rm -rf {} +
    find . -type d -name "*.egg-info" -prune -exec rm -rf {} +

# Show effective UAV_* environment variables
env-show:
    @env | grep '^UAV_' | sort || echo "(no UAV_* env vars set)"
