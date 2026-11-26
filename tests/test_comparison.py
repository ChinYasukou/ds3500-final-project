"""Player comparison requests against a small, hand-checkable SQLite fixture."""

import sqlite3
from contextlib import closing

import pytest
from fastapi.testclient import TestClient

from api.cache import ResponseCache, response_cache
from api.main import app
from api.storage import initialize_database


@pytest.fixture
def comparison_client(tmp_path, monkeypatch):
    database = tmp_path / "nba.sqlite3"
    initialize_database(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.executemany(
            "INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("2024-25", "BOS", "Boston Celtics", "East", 61, 21),
                ("2023-24", "BOS", "Boston Celtics", "East", 64, 18),
            ],
        )
        connection.executemany(
            "INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("2024-25", "p1", "Luka Dončić", 50, 28.16, 8.2, 7.7),
                ("2024-25", "p2", "Example Player", 60, 20.5, 5.0, 4.0),
                ("2024-25", "p3", "Third Player", 70, 12.0, 3.0, 2.0),
                ("2023-24", "p1", "Luka Dončić", 70, 33.9, 9.2, 9.8),
                ("2023-24", "p2", "Example Player", 65, 18.0, 6.0, 5.0),
            ],
        )
    monkeypatch.setenv("NBA_DB_PATH", str(database))
    response_cache.clear()
    with TestClient(app) as client:
        yield client, database
    response_cache.clear()


def test_comparison_returns_selected_season_and_request_order(comparison_client):
    client, _ = comparison_client
    response = client.get(
        "/comparison",
        params={"season": "2024-25", "player_a": "p2", "player_b": "p1"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "season": "2024-25",
        "players": [
            {
                "player_id": "p2",
                "player_name": "Example Player",
                "games_played": 60,
                "points_per_game": 20.5,
                "rebounds_per_game": 5.0,
                "assists_per_game": 4.0,
            },
            {
                "player_id": "p1",
                "player_name": "Luka Dončić",
                "games_played": 50,
                "points_per_game": 28.16,
                "rebounds_per_game": 8.2,
                "assists_per_game": 7.7,
            },
        ],
    }


@pytest.mark.parametrize(
    "changes, status, detail",
    [
        ({"player_b": "p1"}, 422, "Choose two different players"),
        ({"player_b": "unknown"}, 404, "Player not found"),
        ({"season": "2022-23"}, 404, "Season not found"),
    ],
)
def test_comparison_reports_invalid_selections(comparison_client, changes, status, detail):
    client, _ = comparison_client
    parameters = {"season": "2024-25", "player_a": "p1", "player_b": "p2"}
    response = client.get("/comparison", params=parameters | changes)
    assert response.status_code == status
    assert detail in response.json()["detail"]


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"season": "2024-25", "player_a": "p1"},
        {"season": "invalid", "player_a": "p1", "player_b": "p2"},
        {"season": "2024-25", "player_a": "", "player_b": "p2"},
        {"season": "2024-25", "player_a": " ", "player_b": "p2"},
    ],
)
def test_comparison_validates_required_parameters(comparison_client, parameters):
    client, _ = comparison_client
    assert client.get("/comparison", params=parameters).status_code == 422


def test_comparison_binds_player_ids_as_sql_values(comparison_client):
    client, database = comparison_client
    response = client.get(
        "/comparison",
        params={"season": "2024-25", "player_a": "p1'OR'1'='1", "player_b": "p2"},
    )
    assert response.status_code == 404
    assert "Player not found" in response.json()["detail"]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 5


def test_comparison_cache_separates_players_order_and_season(comparison_client, monkeypatch):
    from api import comparison

    client, _ = comparison_client
    original_fetch = comparison.fetch_rows
    queries = []

    def count_queries(query, parameters=()):
        queries.append((query, parameters))
        return original_fetch(query, parameters)

    monkeypatch.setattr(comparison, "fetch_rows", count_queries)
    parameters = {"season": "2024-25", "player_a": "p1", "player_b": "p2"}
    first = client.get("/comparison", params=parameters)
    assert first.status_code == 200
    after_first = len(queries)
    assert client.get("/comparison", params=parameters).json() == first.json()
    assert len(queries) == after_first

    swapped = client.get("/comparison", params=parameters | {"player_a": "p2", "player_b": "p1"})
    assert swapped.json()["players"][0]["player_id"] == "p2"
    changed = client.get("/comparison", params=parameters | {"player_b": "p3"})
    assert changed.json()["players"][1]["player_id"] == "p3"
    older = client.get("/comparison", params=parameters | {"season": "2023-24"})
    assert older.json()["players"][0]["points_per_game"] == 33.9
    assert len(queries) > after_first


def test_comparison_cache_expires_and_refreshes_stored_values(comparison_client, monkeypatch):
    from api import comparison

    client, database = comparison_client
    now = [0.0]
    monkeypatch.setattr(comparison, "response_cache", ResponseCache(clock=lambda: now[0]))
    parameters = {"season": "2024-25", "player_a": "p1", "player_b": "p2"}
    assert client.get("/comparison", params=parameters).json()["players"][0]["points_per_game"] == 28.16
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "UPDATE players SET points_per_game = ? WHERE season = ? AND player_id = ?",
            (30.0, "2024-25", "p1"),
        )
    assert client.get("/comparison", params=parameters).json()["players"][0]["points_per_game"] == 28.16
    now[0] = 300
    assert client.get("/comparison", params=parameters).json()["players"][0]["points_per_game"] == 30.0
