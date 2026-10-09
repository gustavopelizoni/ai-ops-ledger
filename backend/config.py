"""Paths for the standalone application."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
DATA_ENV = "AI_OPERATIONS_ROOM_DATA_DIR"


def data_dir() -> Path:
    path = Path(os.environ.get(DATA_ENV) or Path.home() / ".ai-operations-room").expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / "operations-room.db"


def events_path() -> Path:
    return data_dir() / "events.jsonl"
