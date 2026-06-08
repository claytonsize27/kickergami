# AGENTS.md

## Project Overview

Kickergami tracks never-before-seen NFL kicker stat lines from 1970 through present. A combo is:

```text
(xp_made, xp_missed, fg_made, fg_missed, fg_yards_total)
```

The app uses SQLAlchemy ORM models and supports SQLite locally through `DATABASE_URL`, while staying Postgres-compatible for deployment.

## Install

```bash
cd kickergami
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Test

```bash
pytest
```

## Common Commands

```bash
python scripts/backfill_historical.py sample_data/historical_sample.csv
python scripts/backfill_nflverse.py --start-season 1999
python scripts/update_kickergami.py sample_data/current_sample.csv
python scripts/run_scheduled_update.py
python scripts/validate_deployment.py --require-cloud
python scripts/validate_deployment.py --require-posting
python scripts/season_summary.py 2026
```

## Coding Style

- Python 3.11+.
- Prefer type hints for public functions and structured records.
- Keep workflow logic in `app/`; keep CLI concerns in `scripts/`.
- Keep CSV ingestion behind `app/data_sources/` adapters.
- Use SQLAlchemy ORM patterns already present in the project.
- Add focused tests for behavior changes.

## Data Validation

- Do not accept historical rows before 1970; they should be filtered out.
- `xp_attempts` cannot be less than `xp_made`.
- `fg_attempts` cannot be less than `fg_made`.
- If `fg_made > 0`, `fg_made_distances` must be present.
- Distance count must equal `fg_made`.
- `fg_yards_total` sums made field goals only.

## Secrets And Tweet Safety

- Never commit real API keys, access tokens, or production `.env` files.
- Keep tweet generation under 280 characters.
- Respect `DRY_RUN=true` and `TWEETS_ENABLED=false`; either setting must prevent real posting.
- Log intended tweets in `tweet_log` even when posting is disabled.

## Scheduling

- `scripts/run_scheduled_update.py` is the unattended entrypoint.
- It expects `KICKERGAMI_CURRENT_CSV` to point to the current completed-games CSV.
- Windows Task Scheduler helpers live under `deploy/windows/`.
- Cron examples live under `deploy/cron/`.
- Scheduled runs are only production-ready when the current CSV is refreshed externally and X credentials are present.
- Public nflverse play-by-play is available through `KICKERGAMI_DATA_SOURCE=nflverse_pbp`.
- nflverse data can lag because hosted data is updated nightly during the season.
- Production should be cloud-only via GitHub Actions or another managed scheduler.
- Do not rely on Windows Scheduled Tasks for production.
