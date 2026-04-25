"""Centralised settings — single source of truth for all UAV_* env vars.

Pydantic-Settings replaces the old `config.py` at the repo root. The legacy
file re-exports from here so existing scripts keep working.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FINE_TUNED = "yolomodel/yolo26_animals/weights/best.pt"


class Settings(BaseSettings):
    """All runtime knobs. Override with UAV_* env vars."""

    model_config = SettingsConfigDict(
        env_prefix="UAV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Inference ---
    model_path: str = Field(default=DEFAULT_FINE_TUNED, alias="UAV_MODEL")
    confidence: float = Field(default=0.4, alias="UAV_CONF", ge=0.0, le=1.0)
    img_size: int = Field(default=640, alias="UAV_IMGSZ", gt=0)
    tracker: str = Field(default="bytetrack.yaml", alias="UAV_TRACKER")
    device: str = Field(default="", alias="UAV_DEVICE")
    process_every_n_frames: int = Field(default=1, alias="UAV_STRIDE", ge=1)

    # --- Video sources ---
    video_path: str = Field(default="videos/testvideo.mp4", alias="UAV_VIDEO")
    camera_index: int = Field(default=0, alias="UAV_CAM")

    # --- API server ---
    api_host: str = Field(default="127.0.0.1", alias="UAV_API_HOST")
    api_port: int = Field(default=8000, alias="UAV_API_PORT", gt=0, lt=65536)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", alias="UAV_LOG_LEVEL"
    )

    # --- Storage ---
    db_path: str = Field(default="uav.db", alias="UAV_DB_PATH")
    output_json_path: str = Field(
        default="output.json",
        alias="UAV_OUTPUT_JSON",
        description="Mirror file for legacy video processors.",
    )

    @property
    def repo_root(self) -> Path:
        return REPO_ROOT

    @property
    def absolute_db_path(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else REPO_ROOT / p

    @property
    def absolute_output_json(self) -> Path:
        p = Path(self.output_json_path)
        return p if p.is_absolute() else REPO_ROOT / p


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a process-wide singleton. Tests can override via dependency_overrides."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
