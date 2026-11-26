"""NBA dashboard API entry point. Feature routers extend the shared catalog."""

from fastapi import FastAPI

from api.catalog import router as catalog_router
from api.comparison import router as comparison_router
from api.storage import fetch_rows

app = FastAPI(title="NBA Interactive Dashboard", version="0.2.0")
app.include_router(catalog_router)
app.include_router(comparison_router)


@app.get("/health")
def health() -> dict:
    """Check schema readiness and return live row counts without caching."""
    counts = fetch_rows(
        "SELECT (SELECT COUNT(*) FROM teams) AS teams, "
        "(SELECT COUNT(*) FROM players) AS players"
    )[0]
    return {"status": "ok", **counts}
