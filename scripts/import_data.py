"""Validate canonical CSVs and atomically replace the supplied NBA seasons."""

import argparse
import csv
from contextlib import closing
import math
import re
import sqlite3
from pathlib import Path

from api.storage import database_path, initialize_database

TEAM_FIELDS = ("season", "team_id", "team_name", "conference", "wins", "losses")
PLAYER_FIELDS = (
    "season", "player_id", "player_name", "games_played",
    "points_per_game", "rebounds_per_game", "assists_per_game",
)


def validate_records(records: list[dict], table: str) -> list[dict]:
    """Return typed copies, rejecting missing, duplicate, or invalid values."""
    fields = TEAM_FIELDS if table == "teams" else PLAYER_FIELDS
    identifier = "team_id" if table == "teams" else "player_id"
    seen = set()
    validated = []
    for number, source in enumerate(records, start=2):
        row = {}
        for field in fields:
            value = source.get(field)
            if value is None or not str(value).strip():
                raise ValueError(f"{table} row {number}: missing {field}")
            row[field] = str(value).strip()
        season = row["season"]
        if not re.fullmatch(r"\d{4}-\d{2}", season) or int(season[-2:]) != (int(season[:4]) + 1) % 100:
            raise ValueError(f"{table} row {number}: invalid season {season!r}")
        key = (season, row[identifier])
        if key in seen:
            raise ValueError(f"Duplicate {table} record: {key}")
        seen.add(key)
        integer_fields = ("wins", "losses") if table == "teams" else ("games_played",)
        for field in integer_fields:
            row[field] = int(row[field])
            if row[field] < 0:
                raise ValueError(f"{table} row {number}: {field} must be nonnegative")
        if table == "teams":
            if row["conference"] not in ("East", "West"):
                raise ValueError(f"teams row {number}: invalid conference")
            if row["wins"] + row["losses"] == 0:
                raise ValueError(f"teams row {number}: team must have played a game")
        else:
            if row["games_played"] == 0:
                raise ValueError(f"players row {number}: games_played must be positive")
            for field in PLAYER_FIELDS[4:]:
                row[field] = float(row[field])
                if not math.isfinite(row[field]) or row[field] < 0:
                    raise ValueError(f"players row {number}: {field} must be finite and nonnegative")
        validated.append(row)
    if not validated:
        raise ValueError(f"{table} file contains no records")
    return validated


def read_records(path: Path, table: str) -> list[dict]:
    fields = TEAM_FIELDS if table == "teams" else PLAYER_FIELDS
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, strict=True)
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: required columns are {', '.join(fields)}")
        records = list(reader)
    return validate_records(records, table)


def import_data(teams_path: Path, players_path: Path, database: Path) -> dict:
    teams = read_records(teams_path, "teams")
    players = read_records(players_path, "players")
    seasons = {row["season"] for row in teams}
    if seasons != {row["season"] for row in players}:
        raise ValueError("Team and player files must contain the same seasons")
    initialize_database(database)
    with closing(sqlite3.connect(database)) as connection, connection:
        # Explicit BEGIN keeps both deletions and both insertions in one transaction.
        connection.execute("BEGIN IMMEDIATE")
        for season in sorted(seasons):
            connection.execute("DELETE FROM teams WHERE season = ?", (season,))
            connection.execute("DELETE FROM players WHERE season = ?", (season,))
        connection.executemany(
            "INSERT INTO teams VALUES (:season, :team_id, :team_name, :conference, :wins, :losses)",
            teams,
        )
        connection.executemany(
            "INSERT INTO players VALUES (:season, :player_id, :player_name, :games_played, "
            ":points_per_game, :rebounds_per_game, :assists_per_game)",
            players,
        )
    return {"teams": len(teams), "players": len(players)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teams", type=Path, default=Path("data/processed/teams.csv"))
    parser.add_argument("--players", type=Path, default=Path("data/processed/players.csv"))
    parser.add_argument("--database", type=Path, default=database_path())
    args = parser.parse_args()
    try:
        counts = import_data(args.teams, args.players, args.database)
    except (OSError, ValueError, csv.Error, sqlite3.Error) as error:
        parser.exit(1, f"Import failed: {error}\n")
    print(f"Imported {counts['teams']} teams and {counts['players']} players into {args.database}")
    print("Restart the FastAPI process after a data import to clear cached responses.")


if __name__ == "__main__":
    main()
