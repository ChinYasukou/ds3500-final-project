"""Compare two players' season averages using stored NBA data."""

from fastapi import APIRouter, HTTPException, Query

from api.cache import query_cache_key, response_cache
from api.storage import fetch_rows

router = APIRouter()


@router.get("/comparison")
def compare_players(
    season: str = Query(pattern=r"^\d{4}-\d{2}$"),
    player_a: str = Query(min_length=1, pattern=r"^\S+$"),
    player_b: str = Query(min_length=1, pattern=r"^\S+$"),
) -> dict:
    """Return both players in selection order, preserving stored precision."""
    if player_a == player_b:
        raise HTTPException(status_code=422, detail="Choose two different players")

    def calculate():
        seasons = fetch_rows(
            "SELECT season FROM teams WHERE season = ? LIMIT 1", (season,)
        )
        if not seasons:
            raise HTTPException(status_code=404, detail="Season not found")
        rows = fetch_rows(
            "SELECT player_id, player_name, games_played, points_per_game, "
            "rebounds_per_game, assists_per_game FROM players "
            "WHERE season = ? AND player_id IN (?, ?)",
            (season, player_a, player_b),
        )
        by_id = {row["player_id"]: row for row in rows}
        missing = [player for player in (player_a, player_b) if player not in by_id]
        if missing:
            raise HTTPException(status_code=404, detail=f"Player not found: {', '.join(missing)}")
        return {"season": season, "players": [by_id[player_a], by_id[player_b]]}

    key = query_cache_key(
        "comparison", season=season, player_a=player_a, player_b=player_b
    )
    return response_cache.get_or_compute(key, calculate)
