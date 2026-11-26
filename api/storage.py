"""Shared SQLite path and non-destructive schema initialization."""

import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def database_path() -> Path:
    return Path(os.environ.get("NBA_DB_PATH", PROJECT_ROOT / "data" / "nba.sqlite3"))


def initialize_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.executescript(schema)


def fetch_rows(query: str, parameters: tuple = ()) -> list[dict]:
    """Read stored data with bound values and close the connection after use."""
    try:
        uri = database_path().resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, parameters).fetchall()]
    except sqlite3.Error as error:
        logging.getLogger(__name__).warning("Database query failed: %s", error)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Run python -m scripts.import_data and check NBA_DB_PATH.",
        ) from error
