# NBA Interactive Dashboard

DS3500 final project · Team 29 · Interactive Visualization track

An application for basketball fans to explore team records, find player statistical leaders, and compare two players in one completed NBA regular season.

## Team responsibilities

The NBA visualization topic is selected. The assignments below are proposed by Jinghao for team confirmation. Each member owns their feature's API query, Streamlit interaction and chart, input validation, tests, documentation, and live demonstration.

| Member | New feature | User action and useful result | Suggested feature branch | Peer reviewer |
| --- | --- | --- | --- | --- |
| Jinghao Shen | Player comparison | Select two players and compare points, rebounds, and assists per game in grouped bars and a table. | `feature/player-comparison` | Sebastian |
| Sebastian Brookes | Team standings | Select East, West, or all teams and view wins, losses, win percentage, and a win-percentage bar chart. | `feature/team-standings` | Zexian |
| Zexian Li | Player leaderboards | Select points, rebounds, or assists per game and a minimum games played threshold to view the top 10 players. | `feature/player-leaderboards` | Jinghao |

Additional shared work is distributed as follows.

- Jinghao coordinates the application shell, shared cache helper, integration, and submission checklist.
- Sebastian checks the team data source, conference labels, team records, and standings explanations.
- Zexian checks the player data source, prepares the CSV import script for both tables, and handles player aggregation rules. Sebastian supplies the verified team mapping and Jinghao reviews the import integration.
- All three review a teammate's PR, run the application locally, and write their own feature test. Shared setup work is tracked separately from individual new features.

## Scope and current status

Use one completed regular season, with team season records and player season averages. The proposed season is **2024–25**, pending confirmation that a reusable dataset supplies both tables. Use a fixed downloaded snapshot for reproducible local demonstrations.

| Component | Status |
| --- | --- |
| Shared Python environment and pinned dependencies | Included |
| SQLite table definitions and repeatable schema initialization | Included |
| FastAPI `/health` endpoint reading SQLite row counts | Included |
| Streamlit page with a real HTTP connection check | Included |
| Infrastructure tests | Included |
| Verified source dataset, source URL, license, and download instructions | Pending |
| CSV validation and transactional import | Pending |
| Three analysis endpoints, controls, and charts | Pending |
| Parameter-aware API response cache with TTL | Pending |
| Individual feature tests, peer reviews, and demonstrations | Pending |

## Architecture

```text
Verified source files -> validation/import script -> SQLite
                                                     ^
                                                     |
Streamlit controls -> HTTP requests -> FastAPI -> SQL + analysis/cache
        ^                                 |
        |----------- JSON results --------|
```

The API owns database access and analysis. Streamlit requests results over HTTP and renders them. Reuse suitable validation, logging, error handling, SQL, and cache patterns from MPs 1–3, adapting them to the NBA fields. Run both services locally.

## Quick start for the foundation

Run commands from the repository root. The foundation was verified with Python 3.14. Use that version to reproduce the pinned environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.init_db
python -m pytest -q
```

Initialize the database once before starting the API. Running initialization again preserves existing records. This command creates empty tables. The CSV templates contain headers, and NBA records will be added through the upcoming import work.

Start FastAPI in one terminal with the virtual environment activated.

```bash
python -m uvicorn api.main:app --reload
```

Start Streamlit in a second terminal from the same root, activating the same environment.

```bash
source .venv/bin/activate
python -m streamlit run ui/app.py
```

Open Streamlit at <http://localhost:8501> and click **Check API and database connection**. A fresh database reports zero team and player records. FastAPI's interactive documentation is at <http://127.0.0.1:8000/docs>.

Optional environment variables are `NBA_DB_PATH` for the SQLite file and `NBA_API_URL` for the API base URL. Defaults are `data/nba.sqlite3` and `http://127.0.0.1:8000`. Set the same `NBA_DB_PATH` in initialization and API terminals. Relative database paths resolve from the working directory.

## Repository layout

```text
api/
  main.py                 FastAPI entry point and readiness endpoint
  storage.py              Shared database path and schema initialization
  schema.sql              Team and player tables
ui/
  app.py                  Streamlit entry point and HTTP connection check
scripts/
  init_db.py              Create the SQLite schema
  __init__.py
data/templates/
  teams.csv               Target team CSV header
  players.csv             Target player CSV header
tests/
  test_foundation.py      Shared infrastructure tests
requirements.txt          Pinned Python dependencies
```

Place future feature endpoints in `api/standings.py`, `api/leaderboards.py`, and `api/comparison.py`, and register their routers in `api/main.py`. Place their UI sections in matching modules under `ui/`. Coordinate edits to the shared entry points through small PRs.

## Data preparation and agreed fields

Before feature coding, confirm the source and its reuse terms, season, regular-season filter, download URL, original column names, and mapping to the template headers. Record the source attribution, retrieval date, units, and exact download/import commands here when verified. The data source is still open. The current foundation can be run with its empty database.

| SQLite table | Fields | Uniqueness |
| --- | --- | --- |
| `teams` | `season`, `team_id`, `team_name`, `conference`, `wins`, `losses` | `(season, team_id)` |
| `players` | `season`, `player_id`, `player_name`, `games_played`, `points_per_game`, `rebounds_per_game`, `assists_per_game` | `(season, player_id)` |

Use stable player IDs to distinguish players with the same name. Store `East` or `West` as conference values. Store season labels consistently, such as `2024-25`. Derive win percentage as `wins / (wins + losses)`, guarding against a zero denominator.

Keep one full-season record for each player. For traded players, prefer the source's combined season row and exclude team stint rows. If combined rows must be calculated, derive averages from season totals and games played. Preserve missing values for validation and resolve them explicitly before insertion. Validate required columns, numeric values, positive player games played, and duplicate keys.

The import owner will add `scripts/import_data.py`. The proposed command is `python -m scripts.import_data --teams PATH --players PATH`. Implement and verify this command before adding it to quick start. Validate both files before replacing records and apply changes in one transaction. Reimporting the same snapshot must produce the same stored records. Reload the API after a changed import to clear process-local caches.

## Feature API contracts and acceptance checks

These three endpoints are planned. Agree on their JSON fields before implementing the UI.

| Feature | Planned request | Response content | Acceptance checks |
| --- | --- | --- | --- |
| Standings | `GET /standings?season=2024-25&conference=East` | Season, selected conference, ordered teams with wins, losses, and win percentage | Filter correctly, calculate percentages correctly, order descending by percentage, break ties by team name. Describe this as statistical ordering when ties occur. |
| Leaderboards | `GET /leaderboards?season=2024-25&metric=points_per_game&min_games=20` | Season, metric, threshold, top 10 player IDs, names, games, and metric values | Whitelist the three metrics, apply games threshold before ranking, sort descending with player ID as a tie-breaker. |
| Comparison | `GET /comparison?season=2024-25&player_a=ID_A&player_b=ID_B` | Season and two identified players with all three per-game metrics and games played | Return the selected players' values, reject duplicate selections, and report unknown player IDs. |

The two player feature owners jointly add an API-backed player selector using IDs and names, for example `GET /players?season=2024-25`. Query parameters determine SQL values through bound parameters. Whitelist metric identifiers before choosing a SQL column.

Use FastAPI validation for invalid choices, invalid numbers, and malformed requests. Return 404 for an unknown season or selected player, and an empty items list for valid filters with zero qualifying results. The UI should explain empty results, connection failures, timeouts, and API validation errors. Keep HTTP request timeouts explicit.

## API caching plan

Jinghao will add one shared API-side TTL cache and each owner will use it in their analysis endpoint. Cache successful analysis responses for **300 seconds**, with keys including the endpoint, season, and every effective parameter. Examples include conference for standings, metric and minimum games for leaderboards, and both player IDs for comparisons. Include the player-selector parameters if that response is cached.

Normalize parameter defaults before constructing keys. Repeated equivalent requests should reuse the cached response, different parameter sets must stay independent, and expired entries must be recomputed. Avoid caching errors. Keep the first version read-only with one API process, and restart it after replacing data. If a future endpoint changes data, invalidate related cached entries after a successful commit.

Add tests for a cache hit avoiding repeated analysis, parameter isolation, and expiration using a controllable clock. Update this section with the actual cache implementation and tests when implemented.

## Reusing course work

Use the existing MP1–3 and class exercises when their behavior fits the NBA task. Keep the shared repository runnable on its own by bringing adapted code and required dependencies into this project.

| Course material in the local DS3500 folder | What to adapt | Owner |
| --- | --- | --- |
| `class-exercise/class8_src/` and `class-exercise/class10_data_validator.py`, plus relevant MP1 validation functions | Required-column checks, numeric cleaning, duplicate handling, and import validation | Zexian, with Sebastian checking team fields |
| `class-exercise/class12_14/`, plus relevant MP2 code | FastAPI validation, error responses, request handling, and logging | Each feature owner |
| `class-exercise/class16_18/check_storage.py` and `main.py`, plus relevant MP3 code | SQLite queries, parameter-aware cache keys, TTL expiration, and invalidation | Jinghao coordinates shared cache, each owner adapts their query |
| `class-exercise/class20_21/api_client.py`, `streamlit_app.py`, and `chart_examples.py` | HTTP requests with parameters and timeouts, Streamlit controls, and charts | Each feature owner |

The starter HTTP check follows the class exercise's `requests.get` → `raise_for_status` → JSON pattern. Apply the same flow to each analysis endpoint. Record substantial adaptations in the feature PR and explain the new NBA behavior and tests.

Jinghao's player-comparison feature specifically includes the two API-backed player selectors, HTTP request, SQLite player lookup, comparison response, grouped bar chart/table, integration with the shared cache, and his own feature tests. Shared cache work also supports the other two endpoints.

## Development workflow

1. **Confirm the input data.** Sebastian and Zexian verify that both tables can be obtained for the same completed regular season. All members agree on scope, fields, source attribution, and the assignments above.
2. **Review and merge the foundation PR.** Another member reviews the starter structure, README, tests, and run commands. Everyone checks out the updated `main` and starts their own feature branch.
3. **Import and validate data.** Zexian builds the importer with Sebastian's team mapping. Test invalid values, duplicates, repeat imports, and rollback on failure. Review this small shared-data PR early so the three features can use the same database.
4. **Build each feature end to end.** Implement the SQL analysis and validation, expose the API response, connect Streamlit over HTTP, render useful results, and write the owner's test. Use small hand-checkable test fixtures.
5. **Add shared caching and integrate.** Jinghao adds the cache with tests. Each owner adopts it. Register all routers, combine UI sections, and resolve shared-file changes in PRs. Confirm all three features work in one application.
6. **Reproduce on a teammate's computer.** Clone the repository, follow the README, acquire data, import, start both services, and run tests. Fix missing instructions and record actual feature/test/PR evidence below.
7. **Submit the progress report and rehearse.** Report completed work, remaining tasks, challenges, and the repository URL. Run each member's live scenario on the presentation computer, including empty and invalid inputs.
8. **Present and finalize.** Each member demonstrates and explains their own feature, its code, tests, chart interpretation, and limitations. Push reviewed final changes and submit the shared repository link through Canvas.

### Feature tests owned by each member

| Owner | Planned test file | Minimum useful behavior to test |
| --- | --- | --- |
| Sebastian | `tests/test_standings.py` | With known East/West fixtures, return only the chosen conference with correct win percentages and ordering. |
| Zexian | `tests/test_leaderboards.py` | Exclude a high-scoring player below the games threshold and verify the selected metric's descending top-10 ordering. |
| Jinghao | `tests/test_comparison.py` | Verify both selected players' three metrics and reject missing or identical player selections. |

Each member must personally write at least one test for their new feature and be able to explain it. Add empty-result and invalid-input tests as appropriate. Infrastructure tests are shared setup evidence. Run `python -m pytest -q` before each PR.

### Git collaboration and commit messages

Use the same shared repository and a separate feature branch for each member. For example, Sebastian's local workflow after foundation merge is as follows.

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/team-standings
# Implement and test the feature, then stage the specific files changed.
git add api/standings.py ui/standings.py tests/test_standings.py
git commit -m "feat(standings): filter teams by conference and plot win percentages"
git push -u origin feature/team-standings
```

Include shared entry-point edits in the staged files when registering the feature. Open a PR to `main` and have the assigned teammate review it before merging. Describe the user action, resulting behavior, changed files, and test command/results. After merging, everyone pulls the updated `main` before starting new work.

Write commits that describe concrete completed work. Suitable examples include the following.

- `feat(data): validate season CSVs and import team and player records atomically`
- `feat(leaderboards): apply minimum games filter and rank player averages`
- `feat(comparison): compare two selected players across points rebounds and assists`
- `test(standings): verify conference filtering and win percentage ordering`
- `feat(cache): reuse parameter-specific analysis responses for 300 seconds`
- `docs(readme): record data download commands and individual feature evidence`

## Timeline and submissions

Dates are in 2026, Eastern Time. Internal targets below are proposed team working dates. Confirm the assigned presentation date and time limit in Canvas.

| Date | Deliverable | Owner |
| --- | --- | --- |
| Nov 25–27 | Confirm assignments and source, review foundation, agree on API fields | All three |
| Nov 28–30 | Review/import the data and implement individual feature queries and tests | Zexian leads import, each member owns their feature |
| Dec 1 | Internal target for one full UI → API → SQLite feature, with the other two in progress | All three |
| Dec 2–3 | Internal target for all three features, cache, and integration tests | All three, Jinghao coordinates |
| **Dec 4** | **Progress Report, 100 points.** One team form with completed work, remaining work, challenges, and repository link | Jinghao proposed submitter, all review |
| Dec 5–6 | Clean-environment setup and presentation rehearsal on the actual demo computer | All three |
| **Dec 7 or Dec 10** | **Demo Testing, 50 points.** One team form on the day before the assigned presentation | Jinghao proposed submitter, all test |
| **Dec 8 or Dec 11** | **Live presentation, 250 points.** Each member demonstrates their own feature | All three |
| **Dec 14** | **Final Deliverable, 300 points.** Push final code and submit one accessible GitHub repository link | Jinghao proposed submitter, all verify |
| **Dec 14** | **Peer Evaluation, 800 default points.** Follow the overview's confidential reporting process for contribution or collaboration concerns | Each member |

The Team Formation Survey was due Nov 20 and is worth 100 points. Overall project milestones total 1,600 points. Canvas provides the actual submission forms and assigned presentation schedule. Prepare for the earlier Dec 8 presentation until the schedule is confirmed.

### Presentation run-through

- Jinghao introduces the user questions and explains Streamlit → HTTP → FastAPI → SQLite plus caching.
- Sebastian selects a conference, shows team records and the win-percentage chart, and explains the calculation and tie ordering.
- Zexian switches the leaderboard metric and minimum games threshold, and explains why the leaders can change.
- Jinghao selects two players, compares the three statistics, and explains the effect of different games played and roles.
- Each member explains their implementation and test. Collectively explain the single-season scope, snapshot date, and the limits of comparing players using only per-game averages.

## Final handoff checklist and contribution evidence

The Nov 23 project overview allocates the final repository's 300 points to **individual contributions and collaboration (200)**, **code organization and reliability (50)**, and **README/reproducibility (50)**. Integrated feature functionality is evaluated in the live presentation. Preserve actual commits, branches, PRs, peer reviews, and tests throughout development.

| Member | Implemented new feature | Actual test path/case | Feature PR | Teammate review |
| --- | --- | --- | --- | --- |
| Jinghao Shen | Pending | Pending | Pending | Pending |
| Sebastian Brookes | Pending | Pending | Pending | Pending |
| Zexian Li | Pending | Pending | Pending | Pending |

- [ ] Three new features beyond MPs 1–3 are implemented in one application.
- [ ] Streamlit uses HTTP to request API analysis and displays returned results.
- [ ] API analysis queries persistent SQLite records.
- [ ] API response caching uses all effective parameters and verified TTL behavior.
- [ ] Data validation, API errors, and UI failure/empty states are handled.
- [ ] Each member's new feature has at least one test written by that member.
- [ ] Each member has feature-branch commits, a PR, and another member's review.
- [ ] README contains verified data attribution, download/import, setup, launch, and test instructions.
- [ ] Contribution table links actual features, tests, PRs, and reviews.
- [ ] A teammate reproduces the application on the presentation computer.
- [ ] Demo Testing, presentation, and final repository submissions are completed.

Project requirements are based on the course's **Final Project Overview**, updated Nov 23, 2026. The PDF is distributed through the course. Confirm subsequent changes and submission details in Canvas.
