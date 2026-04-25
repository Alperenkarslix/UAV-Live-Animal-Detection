"""FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache

from uav.core.config import Settings, get_settings
from uav.db.repository import WorldStateRepository

from .state_bus import StateBus


@lru_cache
def _bus() -> StateBus:
    return StateBus()


@lru_cache
def _repo() -> WorldStateRepository:
    settings = get_settings()
    return WorldStateRepository(settings.absolute_db_path)


def get_repo() -> WorldStateRepository:
    return _repo()


def get_bus() -> StateBus:
    return _bus()


def settings_dep() -> Settings:
    return get_settings()
