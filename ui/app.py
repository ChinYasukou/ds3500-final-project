"""Streamlit entry point for the team's shared NBA dashboard."""

import requests
import streamlit as st

if __package__:
    from .api_client import fetch_json
else:
    from api_client import fetch_json

st.set_page_config(page_title="NBA Interactive Dashboard", page_icon="🏀")
st.title("🏀 NBA Interactive Dashboard")
st.info("Shared NBA data and setup are ready. The three analysis features are in development.")

if st.button("Check API and database connection"):
    try:
        status = fetch_json("/health")
        st.success("Connected to FastAPI and SQLite.")
        st.write(f"Team records: {status['teams']} · Player records: {status['players']}")
    except requests.RequestException:
        st.error(
            "Start FastAPI, initialize the database, and check NBA_API_URL. "
            "The connection check could not complete."
        )
    except (ValueError, KeyError, TypeError):
        st.error("The API returned an unexpected health response. Check the API logs.")
