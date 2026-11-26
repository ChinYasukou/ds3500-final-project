"""Exercise the Streamlit comparison controls and returned API results."""

import json
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "ui/app.py"
PLAYERS = [
    {"player_id": "p1", "player_name": "LeBron James", "games_played": 70,
     "points_per_game": 24.4, "rebounds_per_game": 7.8, "assists_per_game": 8.2},
    {"player_id": "p2", "player_name": "Stephen Curry", "games_played": 70,
     "points_per_game": 24.5, "rebounds_per_game": 4.4, "assists_per_game": 6.0},
    {"player_id": "p3", "player_name": "Luka Dončić", "games_played": 50,
     "points_per_game": 28.2, "rebounds_per_game": 8.2, "assists_per_game": 7.7},
]


def response_for(payload, status=200):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode("utf-8")
    return response


@pytest.fixture
def api_calls(monkeypatch):
    calls = []

    def get(url, params=None, timeout=None):
        endpoint = urlparse(url).path
        calls.append((endpoint, params, timeout))
        if endpoint == "/seasons":
            return response_for({"items": ["2024-25"]})
        if endpoint == "/players":
            return response_for({
                "season": params["season"],
                "items": [{"player_id": p["player_id"], "player_name": p["player_name"]} for p in PLAYERS],
            })
        if endpoint == "/comparison":
            by_id = {p["player_id"]: p for p in PLAYERS}
            return response_for({
                "season": params["season"],
                "players": [by_id[params["player_a"]], by_id[params["player_b"]]],
            })
        if endpoint == "/health":
            return response_for({"status": "ok", "teams": 30, "players": 569})
        raise AssertionError(f"Unexpected endpoint {endpoint}")

    monkeypatch.setattr(requests, "get", get)
    return calls


def test_comparison_page_displays_chart_and_api_values(api_calls):
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not page.exception
    assert len(page.selectbox) == 3
    assert len(page.get("vega_lite_chart")) == 1
    table = page.dataframe[0].value
    assert list(table.columns) == ["Statistic", "LeBron James", "Stephen Curry"]
    assert table.iloc[0].tolist() == ["Points per game", "24.4", "24.5"]
    assert table.iloc[3].tolist() == ["Games played", "70", "70"]
    comparison_calls = [call for call in api_calls if call[0] == "/comparison"]
    assert comparison_calls[-1][1] == {"season": "2024-25", "player_a": "p1", "player_b": "p2"}
    assert comparison_calls[-1][2] == 5


def test_changing_player_updates_http_request_and_results(api_calls):
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    page.selectbox[1].set_value("p3").run()
    assert not page.exception
    table = page.dataframe[0].value
    assert list(table.columns) == ["Statistic", "Luka Dončić", "Stephen Curry"]
    assert table.iloc[0].tolist() == ["Points per game", "28.2", "24.5"]
    comparison_calls = [call for call in api_calls if call[0] == "/comparison"]
    assert comparison_calls[-1][1]["player_a"] == "p3"
    assert comparison_calls[-1][1]["player_a"] != comparison_calls[-1][1]["player_b"]


def test_second_selector_excludes_first_player(api_calls):
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert "LeBron James" not in page.selectbox[2].options
    page.selectbox[1].set_value("p2").run()
    assert not page.exception
    assert "Stephen Curry" not in page.selectbox[2].options
    comparison_calls = [call for call in api_calls if call[0] == "/comparison"]
    assert comparison_calls[-1][1]["player_a"] != comparison_calls[-1][1]["player_b"]


def test_comparison_page_handles_api_connection_failure(monkeypatch):
    def disconnected(*args, **kwargs):
        raise requests.ConnectionError("unavailable")

    monkeypatch.setattr(requests, "get", disconnected)
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not page.exception
    assert "Could not load player comparisons" in page.error[0].value
    assert not page.dataframe


def test_comparison_page_handles_empty_seasons(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: response_for({"items": []}))
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not page.exception
    assert "No seasons available" in page.info[0].value
    assert not page.selectbox


def test_comparison_page_handles_too_few_players(monkeypatch):
    def get(url, **kwargs):
        if urlparse(url).path == "/seasons":
            return response_for({"items": ["2024-25"]})
        return response_for({"items": [{"player_id": "p1", "player_name": "Only Player"}]})

    monkeypatch.setattr(requests, "get", get)
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not page.exception
    assert "At least two players" in page.info[0].value


def test_comparison_page_reports_api_error(api_calls, monkeypatch):
    get = requests.get

    def failing_comparison(url, **kwargs):
        if urlparse(url).path == "/comparison":
            return response_for({"detail": "Season not found"}, status=404)
        return get(url, **kwargs)

    monkeypatch.setattr(requests, "get", failing_comparison)
    page = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not page.exception
    assert "Could not load player comparisons" in page.error[0].value
    assert not page.dataframe
