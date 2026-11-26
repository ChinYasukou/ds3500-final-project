"""Shared season and player selectors for the three dashboard features."""

from fastapi import APIRouter, HTTPException, Query

from api.cache import query_cache_key, response_cache
from api.storage import fetch_rows

router = APIRouter()


@router.get("/seasons")
def seasons() -> dict:
    def calculate():
        rows = fetch_rows("SELECT season FROM teams INTERSECT SELECT season FROM players ORDER BY season DESC")
        return {"items": [row["season"] for row in rows]}

    return response_cache.get_or_compute(query_cache_key("seasons"), calculate)


@router.get("/players")
def players(season: str = Query(pattern=r"^\d{4}-\d{2}$")) -> dict:
    def calculate():
        records = fetch_rows("SELECT season FROM teams WHERE season = ? LIMIT 1", (season,))
        if not records:
            raise HTTPException(status_code=404, detail="Season not found")
        rows = fetch_rows(
            "SELECT player_id, player_name FROM players WHERE season = ? "
            "ORDER BY player_name COLLATE NOCASE, player_id", (season,),
        )
        return {"season": season, "items": rows}

    key = query_cache_key("players", season=season)
    return response_cache.get_or_compute(key, calculate)
