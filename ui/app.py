"""Streamlit entry point for the team's shared NBA dashboard."""

import os

import requests
import streamlit as st

st.set_page_config(page_title="NBA Interactive Dashboard", page_icon="🏀")
st.title("🏀 NBA Interactive Dashboard")
st.info("Project setup is ready. NBA data and the three analysis features are pending.")

api_base_url = os.environ.get("NBA_API_URL", "http://127.0.0.1:8000").rstrip("/")
if st.button("Check API and database connection"):
    try:
        response = requests.get(f"{api_base_url}/health", timeout=5)
        response.raise_for_status()
        status = response.json()
        st.success("Connected to FastAPI and SQLite.")
        st.write(f"Team records: {status['teams']} · Player records: {status['players']}")
    except requests.RequestException:
        st.error(
            "Start FastAPI, initialize the database, and check NBA_API_URL. "
            "The connection check could not complete."
        )
    except (ValueError, KeyError, TypeError):
        st.error("The API returned an unexpected health response. Check the API logs.")
