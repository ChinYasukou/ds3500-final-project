"""Run from the repository root with python -m scripts.init_db."""

from api.storage import database_path, initialize_database


def main() -> None:
    path = database_path()
    initialize_database(path)
    print(f"SQLite schema ready at {path}")


if __name__ == "__main__":
    main()
