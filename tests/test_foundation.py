"""Shared infrastructure tests; each member will add feature-specific tests."""

import importlib
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_database_initialization_preserves_existing_data(tmp_path):
    storage = importlib.import_module("api.storage")
    database = tmp_path / "nba.sqlite3"
    storage.initialize_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?)",
            ("2024-25", "BOS", "Boston", "East", 61, 21),
        )
    storage.initialize_database(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT wins FROM teams").fetchall() == [(61,)]
        assert connection.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 0


def test_database_rejects_invalid_records(tmp_path):
    storage = importlib.import_module("api.storage")
    database = tmp_path / "nba.sqlite3"
    storage.initialize_database(database)
    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?)",
                ("2024-25", "BOS", "Boston", "East", -1, 21),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("2024-25", "player-1", "Test Player", 0, 10, 2, 3),
            )


def test_health_reports_missing_database_without_creating_it(tmp_path, monkeypatch):
    database = tmp_path / "missing.sqlite3"
    monkeypatch.setenv("NBA_DB_PATH", str(database))
    app = importlib.import_module("api.main").app
    response = TestClient(app).get("/health")
    assert response.status_code == 503
    assert not database.exists()


def test_health_reads_counts_from_sqlite(tmp_path, monkeypatch):
    storage = importlib.import_module("api.storage")
    database = tmp_path / "nba.sqlite3"
    storage.initialize_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO teams VALUES (?, ?, ?, ?, ?, ?)",
            ("2024-25", "BOS", "Boston", "East", 61, 21),
        )
    monkeypatch.setenv("NBA_DB_PATH", str(database))
    app = importlib.import_module("api.main").app
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "teams": 1, "players": 0}


def test_streamlit_renders_connection_failure(monkeypatch):
    import requests
    from streamlit.testing.v1 import AppTest

    def disconnected(*args, **kwargs):
        raise requests.ConnectionError("API unavailable")

    monkeypatch.setattr(requests, "get", disconnected)
    page = AppTest.from_file(Path(__file__).resolve().parents[1] / "ui/app.py", default_timeout=10).run()
    page.button[0].click().run()
    assert not page.exception
    assert any("Start FastAPI" in error.value for error in page.error)
