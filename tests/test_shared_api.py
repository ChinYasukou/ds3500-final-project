"""Shared selector APIs and cache behavior, independent of personal features."""

import importlib
import sqlite3

from fastapi.testclient import TestClient


def test_response_cache_isolates_keys_expires_and_copies_results():
    cache_class = importlib.import_module("api.cache").ResponseCache
    now = [0.0]
    calls = []
    cache = cache_class(ttl=300, max_entries=2, clock=lambda: now[0])

    def calculate():
        calls.append(True)
        return {"items": [len(calls)]}

    first = cache.get_or_compute(("players", "2024-25"), calculate)
    first["items"].append(999)
    assert cache.get_or_compute(("players", "2024-25"), calculate) == {"items": [1]}
    assert len(calls) == 1
    assert cache.get_or_compute(("players", "2023-24"), calculate) == {"items": [2]}
    now[0] = 300
    assert cache.get_or_compute(("players", "2024-25"), calculate) == {"items": [3]}
    cache.clear()
    assert cache.get_or_compute(("players", "2024-25"), calculate) == {"items": [4]}


def test_selector_endpoints_use_database_and_validate_season(tmp_path, monkeypatch):
    storage = importlib.import_module("api.storage")
    database = tmp_path / "nba.sqlite3"
    storage.initialize_database(database)
    with sqlite3.connect(database) as connection:
        connection.executemany("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("2024-25", "p2", "Z Player", 50, 10, 2, 3),
            ("2024-25", "p1", "A Player", 60, 20, 4, 5),
        ])
        connection.execute("INSERT INTO teams VALUES ('2024-25', 'BOS', 'Boston', 'East', 61, 21)")
    monkeypatch.setenv("NBA_DB_PATH", str(database))
    client = TestClient(importlib.import_module("api.main").app)
    assert client.get("/seasons").json() == {"items": ["2024-25"]}
    response = client.get("/players", params={"season": "2024-25"})
    assert response.status_code == 200
    assert response.json() == {"season": "2024-25", "items": [{"player_id": "p1", "player_name": "A Player"}, {"player_id": "p2", "player_name": "Z Player"}]}
    assert client.get("/players", params={"season": "2023-24"}).status_code == 404
    assert client.get("/players", params={"season": "invalid"}).status_code == 422
    assert client.get("/players").status_code == 422


def test_cache_retries_errors_and_respects_capacity():
    import pytest

    cache_class = importlib.import_module("api.cache").ResponseCache
    cache = cache_class(max_entries=1)
    attempts = []

    def failing():
        attempts.append(True)
        raise ValueError("invalid request")

    for _ in range(2):
        with pytest.raises(ValueError):
            cache.get_or_compute(("bad",), failing)
    assert len(attempts) == 2
    assert cache.get_or_compute(("first",), lambda: 1) == 1
    assert cache.get_or_compute(("second",), lambda: 2) == 2
    assert cache.get_or_compute(("first",), lambda: 3) == 3


def test_concurrent_requests_reuse_one_calculation():
    from concurrent.futures import ThreadPoolExecutor

    cache_class = importlib.import_module("api.cache").ResponseCache
    cache = cache_class()
    calls = []

    def calculate():
        calls.append(True)
        return {"items": [1]}

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: cache.get_or_compute(("same",), calculate), range(8)))
    assert results == [{"items": [1]}] * 8
    assert len(calls) == 1
