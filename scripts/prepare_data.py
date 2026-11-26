"""Verify pinned source snapshots and produce canonical regular-season CSVs."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import requests

from api.storage import PROJECT_ROOT
from scripts.import_data import PLAYER_FIELDS, TEAM_FIELDS, validate_records

EAST = {"ATL", "BKN", "BOS", "CHA", "CHI", "CLE", "DET", "IND", "MIA", "MIL", "NYK", "ORL", "PHI", "TOR", "WAS"}
WEST = {"DAL", "DEN", "GSW", "HOU", "LAC", "LAL", "MEM", "MIN", "NOP", "OKC", "PHX", "POR", "SAC", "SAS", "UTA"}
MANIFEST_PATH = PROJECT_ROOT / "data/manifest.json"


def prepare_data(source_dir: Path, output_dir: Path) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source_tables = []
    for entry in manifest["files"]:
        path = source_dir / Path(entry["path"]).name
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ValueError(f"Snapshot checksum mismatch: {path}")
        with path.open(newline="", encoding="utf-8-sig") as handle:
            records = list(csv.DictReader(handle))
        if len(records) != entry["rows"]:
            raise ValueError(f"Snapshot row count mismatch: {path}")
        source_tables.append(records)

    teams = []
    for row in source_tables[0]:
        if row["team"] not in EAST | WEST:
            raise ValueError(f"Unknown team code: {row['team']}")
        teams.append({
            "season": row["season"], "team_id": row["team"], "team_name": row["team_name"],
            "conference": "East" if row["team"] in EAST else "West",
            "wins": row["wins"], "losses": row["losses"],
        })
    players = []
    for row in source_tables[1]:
        # The source has one full-season row per name and supplies no NBA player ID.
        # Use a reproducible snapshot ID, rejecting duplicate keys in validation.
        player_id = "bsl_" + hashlib.sha256(row["player_name"].encode("utf-8")).hexdigest()[:16]
        games = int(row["games_played"])
        if games <= 0:
            raise ValueError(f"Invalid games_played for {row['player_name']}")
        players.append({
            "season": row["season"], "player_id": player_id, "player_name": row["player_name"],
            "games_played": games, "points_per_game": int(row["points"]) / games,
            "rebounds_per_game": int(row["rebounds"]) / games,
            "assists_per_game": int(row["assists"]) / games,
        })
    tables = [validate_records(teams, "teams"), validate_records(players, "players")]
    if {row["season"] for rows in tables for row in rows} != {manifest["season"]}:
        raise ValueError("Source rows differ from the pinned season")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, fields, rows in zip(("teams", "players"), (TEAM_FIELDS, PLAYER_FIELDS), tables):
        with (output_dir / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda row: tuple(row[field] for field in fields[:2])))


def download_sources(source_dir: Path) -> None:
    """Restore the exact pinned files, failing before writes if upstream changes."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    downloaded = []
    for entry in manifest["files"]:
        response = requests.get(entry["url"], timeout=30)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != entry["sha256"]:
            raise ValueError("Upstream snapshot changed. Use the committed data/source files.")
        downloaded.append((Path(entry["path"]).name, response.content))
    source_dir.mkdir(parents=True, exist_ok=True)
    for name, content in downloaded:
        (source_dir / name).write_bytes(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Restore exact pinned source snapshots from their URLs")
    args = parser.parse_args()
    source_dir = PROJECT_ROOT / "data/source"
    try:
        if args.download:
            download_sources(source_dir)
        prepare_data(source_dir, PROJECT_ROOT / "data/processed")
    except (OSError, ValueError, csv.Error, requests.RequestException) as error:
        parser.exit(1, f"Preparation failed: {error}\n")
    print("Verified source checksums and prepared data/processed/teams.csv and players.csv")


if __name__ == "__main__":
    main()
