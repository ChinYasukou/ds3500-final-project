"""Shared SQLite path and non-destructive schema initialization."""

import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def database_path() -> Path:
    return Path(os.environ.get("NBA_DB_PATH", PROJECT_ROOT / "data" / "nba.sqlite3"))


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(path) as connection:
        connection.executescript(schema)
