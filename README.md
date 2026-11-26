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

Shared preparation is implemented on `setup/nba-shared-foundation`. The follow-up responsibilities are as follows.

- Jinghao maintains the application shell and shared cache, and coordinates feature integration and the submission checklist.
- Sebastian reviews the prepared team records and conference mapping, then implements and explains the standings feature.
- Zexian reviews the prepared player data and import rules, then implements and explains the leaderboards feature. The shared importer is already available for everyone to use.
- All three review a teammate's PR, run the application locally, and write their own feature test. Shared setup work is tracked separately from individual new features.

## Scope and current status

The shared dataset is the **2024–25 regular season**, downloaded on Nov 25, 2026. The repository includes the original snapshots and cleaned CSVs for **30 teams and 569 players**. Each teammate can rebuild SQLite from the committed files without a network request. The assignments above remain proposals for the team to confirm.

| Component | Status |
| --- | --- |
| Shared Python environment and pinned dependencies | Included |
| SQLite table definitions and repeatable schema initialization | Included |
| FastAPI `/health` endpoint reading SQLite row counts | Included |
| Streamlit page with a real HTTP connection check | Included |
| Infrastructure, import, snapshot, selector API, and cache tests | Included and passing |
| Verified source snapshots, attribution, checksums, and restore instructions | Included |
| CSV validation and transactional season import | Included |
| Shared `/seasons` and `/players` selector APIs | Included |
| Shared HTTP client and read-only SQLite query helper | Included |
| Three analysis endpoints, controls, and charts | Pending |
| Parameter-aware API response cache with 300-second TTL | Included and connected to selector APIs, ready for feature endpoints |
| Individual feature tests, peer reviews, and demonstrations | Pending |

### Progress checkpoint

Updated Nov 25, 2026. Shared setup is ready for team review. The three personal analysis features are pending.

| Milestone | Status |
| --- | --- |
| Application foundation and shared helpers | Complete |
| Verified dataset and reproducible database import | Complete |
| Sebastian's standings feature and tests | Pending |
| Zexian's leaderboard feature and tests | Pending |
| Jinghao's comparison feature and tests | Pending |
| Integrated feature validation and teammate reproduction | Pending |
| Live demonstration and demo-testing submission | Pending |
| Final contribution evidence and repository submission | Pending |

This is 2 of 8 listed milestones completed. These milestones differ in size. Counts track deliverables and do not estimate grades or hours. Shared infrastructure tests are recorded separately from each member's own feature tests.

### Shared setup verification

On Nov 25, the shared test suite passed **19 tests**. A temporary independent project directory was used to verify source checksums, regenerate identical cleaned CSVs, import the season twice, run all tests, start FastAPI and Streamlit, call the catalog endpoints over HTTP, and use the Streamlit connection button. The API returned 30 teams and 569 players. Optional restoration from the pinned download URLs and `python -m pip check` also passed.

The next handoff step is a teammate reviewing the setup branch and reproducing the same commands on their own computer. Each member's personal feature implementation and tests remain pending.

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
python -m scripts.import_data
python -m pytest -q
```

The import command creates the schema and loads the committed cleaned CSVs. It reports 30 teams and 569 players. Repeating the import replaces only the supplied seasons in one transaction. Stop and restart FastAPI after reimporting data to clear its in-memory cache. `python -m scripts.init_db` remains available to create empty tables for development.

Start FastAPI in one terminal with the virtual environment activated.

```bash
python -m uvicorn api.main:app --reload
```

Start Streamlit in a second terminal from the same root, activating the same environment.

```bash
source .venv/bin/activate
python -m streamlit run ui/app.py
```

Open Streamlit at <http://localhost:8501> and click **Check API and database connection**. After importing the snapshot, the connection check reports 30 team and 569 player records. FastAPI's interactive documentation is at <http://127.0.0.1:8000/docs>.

Optional environment variables are `NBA_DB_PATH` for the SQLite file and `NBA_API_URL` for the API base URL. Defaults are `data/nba.sqlite3` and `http://127.0.0.1:8000`. Set the same `NBA_DB_PATH` in initialization and API terminals. Relative database paths resolve from the working directory.

## Repository layout

```text
api/
  main.py                 FastAPI entry point and readiness endpoint
  catalog.py              Shared season and player-selector endpoints
  storage.py              SQLite initialization and read-only SQL helper
  cache.py                Shared bounded TTL response cache
  schema.sql              Team and player table definitions
ui/
  app.py                  Streamlit entry point and HTTP connection check
  api_client.py           Shared HTTP JSON client with timeout
scripts/
  init_db.py              Create empty SQLite tables
  prepare_data.py         Verify snapshots and rebuild cleaned CSVs
  import_data.py          Validate CSVs and atomically import seasons
data/
  manifest.json           Source URLs, license, row counts, and SHA-256 checksums
  source/                 Committed original CSV snapshots
  processed/              Committed canonical team and player CSVs
  templates/              Canonical CSV headers
tests/
  test_foundation.py      Schema, readiness, and UI failure checks
  test_shared_data.py     Validation, repeat imports, rollback, and snapshot checks
  test_shared_api.py      Selectors, cache hits, expiration, capacity, and concurrency
requirements.txt          Pinned Python dependencies
```

Place future feature endpoints in `api/standings.py`, `api/leaderboards.py`, and `api/comparison.py`, and register their routers in `api/main.py`. Place their UI sections in matching modules under `ui/`. Coordinate edits to the shared entry points through small PRs.

## Data preparation and agreed fields

Source attribution is **BoxScore Lab, data retrieved Nov 25, 2026, underlying statistics from NBA Stats / NBA.com**. The provider publishes the CSVs under **CC BY 4.0**. This project keeps the source snapshots and derives per-game averages and conference labels. [Source and reuse terms](https://boxscorelab.com/downloads/), [provider methodology](https://boxscorelab.com/methodology/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

| Source file | Records | Contents |
| --- | --- | --- |
| `data/source/2024-25-team-standings.csv` | 30 | Team season records |
| `data/source/2024-25-player-season-totals.csv` | 569 | One full-season record per player |

`data/manifest.json` records the download URLs and exact SHA-256 hashes. The preparation script verifies hashes and row counts before converting the snapshots. The committed cleaned files let teammates import and develop offline after installing dependencies.

| SQLite table | Fields | Uniqueness |
| --- | --- | --- |
| `teams` | `season`, `team_id`, `team_name`, `conference`, `wins`, `losses` | `(season, team_id)` |
| `players` | `season`, `player_id`, `player_name`, `games_played`, `points_per_game`, `rebounds_per_game`, `assists_per_game` | `(season, player_id)` |

Preparation renames source `team` to `team_id`, adds an explicit East/West mapping for all 30 teams, and derives each player's per-game values from season totals divided by games played. Keep full precision in SQLite and round when displaying values. Every team has 82 games, each conference has 15 teams, and the sum of wins and losses is 1,230 each.

The source has one combined season row per player, including traded players. Player names are unique within this snapshot. Because the source does not supply NBA player IDs, preparation creates a deterministic `bsl_` ID from the first 16 hexadecimal characters of the player name's UTF-8 SHA-256 hash. These IDs are snapshot identifiers. A future source with duplicate names will require an updated identity mapping. The importer rejects duplicate keys. Preserve Unicode names such as Luka Dončić.

Derive team win percentage as `wins / (wins + losses)`. Import validation rejects missing fields, invalid season labels, negative counts, zero games played, non-finite averages, duplicate keys, and mismatched seasons between the files. Both files are validated before any data replacement. Import uses one transaction for both tables, preserves other seasons, and rolls back the replacement if a database operation fails.

To rebuild cleaned files from the committed source snapshots and reimport them, run the following commands from the repository root.

```bash
python -m scripts.prepare_data
python -m scripts.import_data
```

To restore the exact source snapshots from their URLs, use the optional download command. It verifies the pinned hashes before writing files and reports an error if the upstream contents have changed. The committed snapshots remain available for reproduction.

```bash
python -m scripts.prepare_data --download
```

Custom canonical files can be imported with explicit paths.

```bash
python -m scripts.import_data --teams PATH_TO_TEAMS_CSV --players PATH_TO_PLAYERS_CSV
```

The import also accepts `--database PATH` or the shared `NBA_DB_PATH` environment variable. Restart FastAPI after importing changed data.

## Feature API contracts and acceptance checks

These three endpoints are planned. Agree on their JSON fields before implementing the UI.

| Feature | Planned request | Response content | Acceptance checks |
| --- | --- | --- | --- |
| Standings | `GET /standings?season=2024-25&conference=East` | Season, selected conference, ordered teams with wins, losses, and win percentage | Filter correctly, calculate percentages correctly, order descending by percentage, break ties by team name. Describe this as statistical ordering when ties occur. |
| Leaderboards | `GET /leaderboards?season=2024-25&metric=points_per_game&min_games=20` | Season, metric, threshold, top 10 player IDs, names, games, and metric values | Whitelist the three metrics, apply games threshold before ranking, sort descending with player ID as a tie-breaker. |
| Comparison | `GET /comparison?season=2024-25&player_a=ID_A&player_b=ID_B` | Season and two identified players with all three per-game metrics and games played | Return the selected players' values, reject duplicate selections, and report unknown player IDs. |

Shared selectors are implemented. `GET /seasons` returns `{"items": ["2024-25"]}`. `GET /players?season=2024-25` returns `{"season": "2024-25", "items": [{"player_id": "...", "player_name": "..."}]}` with names ordered alphabetically. Use these IDs in the comparison request. Missing or malformed season parameters produce 422 and unknown seasons produce 404. Database failures produce 503.

Use `api.storage.fetch_rows(sql, parameters)` for read-only SQLite queries with bound values. Whitelist metric identifiers before choosing a SQL column. Use `ui.api_client.fetch_json(endpoint, params)` for UI requests. The client applies a five-second timeout, raises HTTP errors, and validates that JSON is an object. Each feature UI should catch these errors and display a useful message.

Use FastAPI validation for invalid choices, invalid numbers, and malformed requests. Return 404 for an unknown season or selected player, and an empty items list for valid filters with zero qualifying results. The UI should explain empty results, connection failures, timeouts, and API validation errors. Keep HTTP request timeouts explicit.

## Shared API caching

`api/cache.py` implements a thread-safe, process-local response cache with a **300-second TTL** and a maximum of **256 entries**. `/seasons` and `/players` use it. The three feature owners should connect their analysis endpoints to the same helper after validating and defaulting request parameters.

```python
from api.cache import query_cache_key, response_cache

key = query_cache_key("standings", season=season, conference=conference)
result = response_cache.get_or_compute(key, calculate_standings)
```

The key helper includes the database path, endpoint name, and all supplied parameters sorted by name. Include every parameter that changes the result. For leaderboards, include season, metric, and minimum games. For comparisons, include season and both selected player IDs.

The cache reuses successful results, isolates parameter combinations, recomputes expired entries, and returns copied values. Errors are retried on the next request. Concurrent requests for the same key reuse one calculation. `/health` always reads current row counts. Run one API process for this local application and restart it after replacing database contents. `response_cache.clear()` is available for future in-process writes, and must run after a successful data-changing transaction.

Tests in `tests/test_shared_api.py` verify hits, key isolation, exact TTL expiration, explicit clearing, mutation isolation, capacity eviction, error retries, and concurrent requests. Analysis-endpoint integration with this helper is part of each owner's feature work.

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

1. **Review the prepared data and assignments.** The verified 2024–25 snapshots, mappings, importer, and shared tests are ready. Sebastian reviews team records and Zexian reviews player records. All members confirm their feature ownership and API response fields.
2. **Review and merge the foundation PR.** Another member reviews the starter structure, README, tests, and run commands. Everyone checks out the updated `main` and starts their own feature branch.
3. **Load the shared database.** Each teammate runs the documented import and tests, then checks that `/health` returns 30 teams and 569 players. The importer and rollback checks are already implemented.
4. **Build each feature end to end.** Implement the SQL analysis and validation, expose the API response, connect Streamlit over HTTP, render useful results, and write the owner's test. Use small hand-checkable test fixtures.
5. **Use the shared cache and integrate.** Each owner adopts the implemented cache helper for their endpoint. Register all routers, combine UI sections, and resolve shared-file changes in PRs. Confirm all three features work in one application.
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

### Jinghao's comparison feature checklist

The common player catalog, database query helper, HTTP client, and cache are ready to reuse. The following personal feature steps are pending.

- [ ] Implement the two-player SQLite query and comparison API response.
- [ ] Add player selectors and send the selected IDs through the HTTP client.
- [ ] Display grouped bars and a table for the three per-game statistics.
- [ ] Integrate comparison parameters with the shared cache and validate invalid selections.
- [ ] Personally write and explain comparison feature tests.
- [ ] Open a feature PR, obtain peer review, and prepare the live demonstration.

### Git collaboration and commit messages

Use the same shared repository and a separate feature branch for each member. For example, Sebastian's local workflow after foundation merge is as follows.

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/team-standings
# Implement and test the feature, then stage the specific files changed.
git add api/standings.py ui/standings.py tests/test_standings.py
git commit -m "Add conference filters and a win percentage chart"
git push -u origin feature/team-standings
```

Include shared entry-point edits in the staged files when registering the feature. Open a PR to `main` and have the assigned teammate review it before merging. Describe the user action, resulting behavior, changed files, and test command/results. After merging, everyone pulls the updated `main` before starting new work.

Write commits that describe concrete completed work. Suitable examples include the following.

- `Add validation and a repeatable import for team and player data`
- `Filter the player leaderboard by games played and selected statistic`
- `Compare two players across points, rebounds, and assists`
- `Test conference filtering and win percentage ordering`
- `Cache repeated API queries for five minutes`
- `Document data setup and link each member's feature and tests`

## Timeline and submissions

Dates are in 2026, Eastern Time. Internal targets below are proposed team working dates. Confirm the assigned presentation date and time limit in Canvas.

| Date | Deliverable | Owner |
| --- | --- | --- |
| Nov 25–27 | Review implemented shared data and helpers, confirm assignments and API fields | All three |
| Nov 28–30 | Reproduce the shared setup and implement individual feature queries and tests | Each member owns their feature |
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
- [x] README contains verified data attribution, download/import, setup, launch, and test instructions.
- [ ] Contribution table links actual features, tests, PRs, and reviews.
- [ ] A teammate reproduces the application on the presentation computer.
- [ ] Demo Testing, presentation, and final repository submissions are completed.

Project requirements are based on the course's **Final Project Overview**, updated Nov 23, 2026. The PDF is distributed through the course. Confirm subsequent changes and submission details in Canvas.
