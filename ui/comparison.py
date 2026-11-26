"""Streamlit controls and charts for comparing two NBA players."""

import altair as alt
import pandas as pd
import requests
import streamlit as st

if __package__:
    from .api_client import fetch_json
else:
    from api_client import fetch_json

METRICS = {
    "points_per_game": "Points per game",
    "rebounds_per_game": "Rebounds per game",
    "assists_per_game": "Assists per game",
}


def render_comparison() -> None:
    st.subheader("Player comparison")
    try:
        seasons = fetch_json("/seasons")["items"]
        if not seasons:
            st.info("No seasons available. Import the shared dataset and refresh the page.")
            return
        season = st.selectbox("Season", seasons, key="comparison_season")
        players = fetch_json("/players", {"season": season})["items"]
        if len(players) < 2:
            st.info("At least two players are needed to compare this season.")
            return
        names = {player["player_id"]: player["player_name"] for player in players}
        player_ids = list(names)
        default_a = next((key for key in player_ids if names[key] == "LeBron James"), player_ids[0])
        left, right = st.columns(2)
        with left:
            player_a = st.selectbox(
                "First player", player_ids, index=player_ids.index(default_a),
                format_func=names.get, key="comparison_player_a",
            )
        other_ids = [key for key in player_ids if key != player_a]
        default_b = next((key for key in other_ids if names[key] == "Stephen Curry"), other_ids[0])
        with right:
            player_b = st.selectbox(
                "Second player", other_ids, index=other_ids.index(default_b),
                format_func=names.get, key="comparison_player_b",
            )
        result = fetch_json(
            "/comparison", {"season": season, "player_a": player_a, "player_b": player_b}
        )
        compared = result["players"]
        chart_rows = []
        table_data = {"Statistic": [*METRICS.values(), "Games played"]}
        for player in compared:
            table_data[player["player_name"]] = [f"{player[field]:.1f}" for field in METRICS]
            table_data[player["player_name"]].append(str(player["games_played"]))
            for field, label in METRICS.items():
                chart_rows.append({
                    "Player": player["player_name"], "Statistic": label,
                    "Average": player[field], "Games played": player["games_played"],
                })
        selected_names = [player["player_name"] for player in compared]
        chart = alt.Chart(pd.DataFrame(chart_rows)).mark_bar().encode(
            x=alt.X("Statistic:N", sort=list(METRICS.values()), title=None, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Player:N", sort=selected_names),
            y=alt.Y("Average:Q", title="Per game", scale=alt.Scale(zero=True)),
            color=alt.Color(
                "Player:N", scale=alt.Scale(domain=selected_names, range=["#2D6CDF", "#E89B38"]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=["Player:N", "Statistic:N", alt.Tooltip("Average:Q", format=".1f"), "Games played:Q"],
        ).properties(height=330)
        st.altair_chart(chart, width="stretch")
        st.dataframe(pd.DataFrame(table_data), hide_index=True, width="stretch")
        st.caption("Per-game averages do not adjust for playing time, role, or pace.")
        st.caption(
            f"{season} regular season · Data from [BoxScore Lab](https://boxscorelab.com/downloads/) "
            "and NBA Stats."
        )
    except requests.RequestException:
        st.error("Could not load player comparisons. Check that the API is running, then refresh the page.")
    except (KeyError, TypeError, ValueError):
        st.error("The API returned unexpected comparison data. Check the API response and refresh the page.")
