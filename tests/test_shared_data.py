"""Regression checks for shared data preparation and atomic season replacement."""

import csv
import importlib
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEAM = {"season": "2024-25", "team_id": "BOS", "team_name": "Boston Celtics", "conference": "East", "wins": "61", "losses": "21"}
PLAYER = {"season": "2024-25", "player_id": "p1", "player_name": "Example Player", "games_played": "50", "points_per_game": "20", "rebounds_per_game": "5", "assists_per_game": "4"}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_import_is_repeatable_and_preserves_other_seasons(tmp_path):
    importer = importlib.import_module("scripts.import_data")
    database = tmp_path / "nba.sqlite3"
    teams = write_csv(tmp_path / "teams.csv", [TEAM])
    players = write_csv(tmp_path / "players.csv", [PLAYER])
    importer.import_data(teams, players, database)
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO teams VALUES ('2023-24', 'BOS', 'Boston', 'East', 64, 18)")
    importer.import_data(teams, players, database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 1


@pytest.mark.parametrize("change", [{"points_per_game": "NaN"}, {"games_played": "0"}, {"player_name": " "}, {"season": "2024-26"}])
def test_invalid_player_file_leaves_database_unchanged(tmp_path, change):
    importer = importlib.import_module("scripts.import_data")
    database = tmp_path / "nba.sqlite3"
    teams = write_csv(tmp_path / "teams.csv", [TEAM])
    players = write_csv(tmp_path / "players.csv", [PLAYER])
    importer.import_data(teams, players, database)
    write_csv(players, [PLAYER | change])
    with pytest.raises(ValueError):
        importer.import_data(teams, players, database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT player_name FROM players").fetchone()[0] == "Example Player"


def test_duplicate_records_are_rejected_before_replacement(tmp_path):
    importer = importlib.import_module("scripts.import_data")
    teams = write_csv(tmp_path / "teams.csv", [TEAM, TEAM])
    players = write_csv(tmp_path / "players.csv", [PLAYER])
    with pytest.raises(ValueError, match="Duplicate"):
        importer.import_data(teams, players, tmp_path / "nba.sqlite3")


def test_partial_database_failure_rolls_back_both_tables(tmp_path):
    importer = importlib.import_module("scripts.import_data")
    database = tmp_path / "nba.sqlite3"
    teams = write_csv(tmp_path / "teams.csv", [TEAM])
    players = write_csv(tmp_path / "players.csv", [PLAYER])
    importer.import_data(teams, players, database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TRIGGER reject_players BEFORE INSERT ON players BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    write_csv(teams, [TEAM | {"wins": "60", "losses": "22"}])
    with pytest.raises(sqlite3.IntegrityError):
        importer.import_data(teams, players, database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT wins FROM teams").fetchone()[0] == 61
        assert connection.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 1


def test_bundled_snapshot_prepares_complete_unique_season(tmp_path):
    preparation = importlib.import_module("scripts.prepare_data")
    preparation.prepare_data(ROOT / "data/source", tmp_path)
    importer = importlib.import_module("scripts.import_data")
    database = tmp_path / "nba.sqlite3"
    result = importer.import_data(tmp_path / "teams.csv", tmp_path / "players.csv", database)
    assert result == {"teams": 30, "players": 569}
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT SUM(wins), SUM(losses) FROM teams").fetchone() == (1230, 1230)
        assert connection.execute("SELECT conference, COUNT(*) FROM teams GROUP BY conference ORDER BY conference").fetchall() == [("East", 15), ("West", 15)]
        assert connection.execute("SELECT COUNT(*) FROM players WHERE player_name = 'Luka Dončić'").fetchone()[0] == 1
        assert connection.execute("SELECT points_per_game FROM players WHERE player_name = 'Shai Gilgeous-Alexander'").fetchone()[0] == pytest.approx(2484 / 76)
    first = (tmp_path / "players.csv").read_bytes()
    preparation.prepare_data(ROOT / "data/source", tmp_path)
    assert (tmp_path / "players.csv").read_bytes() == first


def test_import_rejects_missing_columns_and_mismatched_seasons(tmp_path):
    importer = importlib.import_module("scripts.import_data")
    database = tmp_path / "nba.sqlite3"
    teams = write_csv(tmp_path / "teams.csv", [TEAM])
    players = write_csv(tmp_path / "players.csv", [{"season": "2024-25"}])
    with pytest.raises(ValueError, match="required columns"):
        importer.import_data(teams, players, database)
    write_csv(players, [PLAYER | {"season": "2023-24"}])
    with pytest.raises(ValueError, match="same seasons"):
        importer.import_data(teams, players, database)
    assert not database.exists()


def test_preparation_rejects_modified_source_files(tmp_path):
    preparation = importlib.import_module("scripts.prepare_data")
    source = tmp_path / "source"
    source.mkdir()
    (source / "2024-25-team-standings.csv").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        preparation.prepare_data(source, tmp_path / "processed")
    assert not (tmp_path / "processed").exists()
