"""HTTP client pattern adapted from class20_21/api_client.py."""

import os

import requests


def fetch_json(endpoint: str, params: dict | None = None) -> dict:
    """Fetch API JSON. Callers display connection, HTTP, or JSON errors in the UI."""
    base_url = os.environ.get("NBA_API_URL", "http://127.0.0.1:8000").rstrip("/")
    response = requests.get(f"{base_url}/{endpoint.lstrip('/')}", params=params, timeout=5)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object from the API")
    return result
