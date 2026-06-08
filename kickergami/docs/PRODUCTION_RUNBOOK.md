# Kickergami Production Runbook

Production Kickergami should run in the cloud, not on this Windows machine. The cloud scheduler is GitHub Actions:

```text
.github/workflows/kickergami-update.yml
```

The old Windows Scheduled Task helpers are kept for development only and should stay disabled for production.

## Current State

Configured as far as possible without private account credentials:

```text
KICKERGAMI_DATA_SOURCE=nflverse_pbp
KICKERGAMI_SKIP_OFFSEASON=true
TWEETS_ENABLED=false
DRY_RUN=true
```

This means the public data feed path is configured, but real posting is intentionally disabled until cloud secrets are present and the posting switches are flipped.

## One-Time Historical Backfill

Kickergami needs a complete combo history before live updates can identify true first occurrences.

1. Prepare the required 1970-1998 normalized CSV.
2. Backfill 1970-1998:

```powershell
cd C:\Users\clayt\OneDrive\Documents\Kickeragami\kickergami
python scripts\backfill_historical.py C:\path\to\historical_1970_1998.csv
```

3. Backfill 1999-present from nflverse:

```powershell
python scripts\backfill_nflverse.py --start-season 1999
```

In GitHub Actions, run:

```text
Actions -> Kickergami nflverse Backfill -> Run workflow
```

The current scheduled updater handles 1999-present public nflverse PBP going forward. The required 1970-1998 data still has to come from a normalized historical file because nflverse PBP starts at 1999.

## X/Twitter Credentials

Create an X developer app with read/write permissions and OAuth 1.0a user-context credentials.

You need these four values:

```text
X_API_KEY
X_API_SECRET
X_ACCESS_TOKEN
X_ACCESS_TOKEN_SECRET
```

Put them in GitHub Actions Secrets:

```text
Repo -> Settings -> Secrets and variables -> Actions -> Secrets
```

Then flip:

```text
TWEETS_ENABLED=true
DRY_RUN=false
```

Do not commit credentials. `.env` is ignored by `.gitignore` and is for local dry-run testing only.

## Validate Before First Real Game Window

Run:

```powershell
cd C:\Users\clayt\OneDrive\Documents\Kickeragami\kickergami
python scripts\validate_deployment.py --require-cloud --require-posting
```

It should end with:

```text
Production checks passed.
```

## Public nflverse Feed

The configured public feed is:

```text
https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz
```

The app derives kicker-game rows from `field_goal` and `extra_point` plays and caches the downloaded season file under:

```text
data/cache/nflverse
```

nflfastR/nflreadr documentation says the hosted data is updated nightly during the season. If a game ends late and the upstream file has not refreshed yet, Kickergami will pick it up on the next scheduled run because inserts are idempotent.

## Cloud Scheduler

The cloud workflow runs at both Eastern daylight and standard UTC equivalents:

```text
Thursday 11:45 PM ET -> Friday 03:45/04:45 UTC
Saturday 11:45 PM ET -> Sunday 03:45/04:45 UTC
Sunday 11:45 PM ET -> Monday 03:45/04:45 UTC
Monday 11:45 PM ET -> Tuesday 03:45/04:45 UTC
```

Duplicate runs are safe because `game_id + player_id` and tweet-log checks prevent double processing/posting.

## Local Windows Tasks

Local Windows tasks are not production. If they exist, disable them:

```powershell
Get-ScheduledTask -TaskName 'Kickergami*' | Disable-ScheduledTask
```

Expected tasks:

```text
Kickergami Thursday 1145PM ET
Kickergami Sunday 1145PM ET
Kickergami Monday 1145PM ET
Kickergami Saturday 1145PM ET
```

## Final Go-Live Checklist

- Historical backfill completed.
- GitHub Secret `DATABASE_URL` points at managed Postgres.
- `KICKERGAMI_DATA_SOURCE=nflverse_pbp`.
- X credentials are present.
- `TWEETS_ENABLED=true`.
- `DRY_RUN=false`.
- `python scripts\validate_deployment.py --require-cloud --require-posting` passes.
- GitHub Actions workflow is enabled.
- Local scheduled tasks are disabled.
