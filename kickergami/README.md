# Kickergami

Kickergami tracks never-before-seen NFL kicker stat lines from completed games.

A Kickergami combo is a unique kicker-game tuple:

```text
(xp_made, xp_missed, fg_made, fg_missed, fg_yards_total)
```

The `combo_key` format is:

```text
{xp_made}-{xp_missed}-{fg_made}-{fg_missed}-{fg_yards_total}
```

For example, 3 extra points made, 0 missed, 4 field goals made, 1 missed, and 177 made-field-goal yards becomes `3-0-4-1-177`.

## Why End-Of-Game Only

The MVP intentionally processes completed games only. Live or halftime tracking needs a different reliability model, because NFL scoring corrections, stat-feed delays, and in-game attribution changes can create false positives. End-of-game updates keep the bot accurate and easier to operate.

## Data Inputs

The MVP supports normalized CSV input for both historical and current completed-game updates. It also supports a public `nflverse_pbp` data source for 1999-present/current completed-game automation.

The normalized CSV schema is:

```text
date
season
week
season_type
game_id
player_id
player_name
team
opponent
xp_made
xp_attempts
fg_made
fg_attempts
fg_made_distances
```

Rules:

- Official historical start year is 1970. Earlier rows are ignored.
- `xp_missed = xp_attempts - xp_made`.
- `fg_missed = fg_attempts - fg_made`.
- `fg_made_distances` is comma-separated, such as `33,45,51`, or blank when `fg_made` is 0.
- If `fg_made > 0` and distances are blank, validation fails.
- If distance count does not equal `fg_made`, validation fails.
- Regular season and playoffs should both be included.

The nflverse path reads season play-by-play CSV files from the public nflverse data release and derives kicker-game lines from `field_goal` and `extra_point` plays.

## Local Setup

Use Python 3.11 or newer.

```bash
cd kickergami
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For local SQLite, copy `.env.example` and keep:

```text
DATABASE_URL=sqlite:///kickergami.db
TWEETS_ENABLED=false
DRY_RUN=true
```

For Postgres, set:

```text
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/kickergami
```

## Historical Backfill

Run one or more normalized historical CSVs:

```bash
python scripts/backfill_historical.py sample_data/historical_sample.csv
```

The backfill processes rows chronologically, inserts `kicker_games`, creates first-seen `kicker_combos`, increments repeat occurrences, updates `season_tracker`, and skips already-seen `game_id + player_id` rows when rerun.

For 1999-present, you can backfill directly from public nflverse PBP without uploading CSVs:

```bash
python scripts/backfill_nflverse.py --start-season 1999
```

In GitHub Actions, run `Kickergami nflverse Backfill` after the 1970-1998 CSV backfill.

## Current Completed-Game Update

After backfill, process a completed-games CSV:

```bash
python scripts/update_kickergami.py sample_data/current_sample.csv
```

New combos are marked as Kickergamis, logged, and tweeted only when posting is enabled. Existing combos increment occurrence count and do not tweet.

For unattended scheduled runs, set `KICKERGAMI_CURRENT_CSV` in `.env` and run:

```bash
python scripts/run_scheduled_update.py
```

That command is what cron, Windows Task Scheduler, or Codex automation should call at the end-of-game windows.

To use the public nflverse play-by-play feed instead of a local current CSV:

```text
KICKERGAMI_DATA_SOURCE=nflverse_pbp
KICKERGAMI_NFLVERSE_SEASON=
KICKERGAMI_NFLVERSE_REFRESH=true
KICKERGAMI_SKIP_OFFSEASON=true
```

Leave `KICKERGAMI_NFLVERSE_SEASON` blank to use the current NFL season. In January and February, the app treats the prior calendar year as the active NFL season.

## Dry Run And Tweeting

Safe defaults are:

```text
TWEETS_ENABLED=false
DRY_RUN=true
```

If `DRY_RUN=true`, the app never posts to X and prints intended tweet text to the console. It still writes `tweet_log` with `tweet_type = dry_run_new_kickergami`.

If `TWEETS_ENABLED=false`, the app never posts to X and writes `tweet_type = new_kickergami_disabled`.

To enable real X/Twitter posting:

```text
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
TWEETS_ENABLED=true
DRY_RUN=false
```

Duplicate tweets are prevented through `tweet_log`.

## Season Summary

```bash
python scripts/season_summary.py 2026
```

This prints the season, total Kickergamis, latest Kickergami, the 10 most recent Kickergamis, and the 10 rarest combos by occurrence count.

## Cron Jobs

Run completed-game updates after game windows have ended. Suggested Eastern Time cron windows:

- Thursday 11:45 PM ET
- Sunday 11:45 PM ET
- Monday 11:45 PM ET
- Saturday 11:45 PM ET during late season/playoffs

Each cron should activate the environment, set env vars, and run `python scripts/run_scheduled_update.py`.

This repo includes deploy helpers:

```powershell
powershell -ExecutionPolicy Bypass -File deploy\windows\install_scheduled_tasks.ps1
```

The Windows installer creates weekly 11:45 PM tasks for Thursday, Sunday, Monday, and Saturday. Make sure the host machine is set to Eastern Time.

For Linux cron, adapt:

```bash
deploy/cron/kickergami.crontab
```

## Deployment Checklist

Before expecting real X/Twitter posts:

- Run the historical backfill against real 1970-present data.
- Set `DATABASE_URL` to the production SQLite/Postgres database.
- Use `KICKERGAMI_DATA_SOURCE=nflverse_pbp`, or set `KICKERGAMI_CURRENT_CSV` to a file that is refreshed after completed NFL games.
- Set real X credentials.
- Set `TWEETS_ENABLED=true`.
- Set `DRY_RUN=false`.
- Install the scheduled tasks or cron on an always-on machine.

Without nflverse network access or a refreshed completed-games CSV, the scheduler will run but has no new game data to process.

## Real Data Feed Notes

The public nflverse feed requires no credentials. The tradeoff is freshness: nflfastR/nflreadr documentation says the hosted data is updated nightly during the season, so a game that ends shortly before the 11:45 PM window may not appear until the upstream release refreshes. The app is idempotent, so repeated weekly checks are safe.

The installed scheduled tasks can remain active all year. With `KICKERGAMI_SKIP_OFFSEASON=true`, the runner exits without downloading data outside January, February, and September-December.

For the tightest possible posting delay, replace or supplement nflverse with a paid/licensed live stats provider that guarantees final box score availability immediately after games.

## Tests

```bash
pytest
```

## Production Validation

```bash
python scripts/validate_deployment.py
python scripts/validate_deployment.py --require-cloud
python scripts/validate_deployment.py --require-posting
```

See [docs/PRODUCTION_RUNBOOK.md](docs/PRODUCTION_RUNBOOK.md) for the full go-live checklist.
See [docs/CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md) for the cloud-only deployment path.
