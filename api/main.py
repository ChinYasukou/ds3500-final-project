"""NBA dashboard API entry point. Analysis routers will be added by feature PRs."""

import logging
import sqlite3

from fastapi import FastAPI, HTTPException

from api.storage import database_path

logger = logging.getLogger(__name__)
app = FastAPI(title="NBA Interactive Dashboard", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Check the database schema and return current business-table row counts."""
    try:
        database_uri = database_path().resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(database_uri, uri=True) as connection:
            teams = connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
            players = connection.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    except sqlite3.Error as error:
        logger.warning("Database readiness check failed: %s", error)
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Run python -m scripts.init_db and check NBA_DB_PATH.",
        ) from error
    return {"status": "ok", "teams": teams, "players": players}
