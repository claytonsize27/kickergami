# Cloud Deployment

Production Kickergami should run fully in the cloud. Do not rely on Windows Task Scheduler, cron on a laptop, or a local SQLite database for production posting.

The recommended MVP cloud stack is:

- GitHub Actions for scheduled execution.
- Neon, Supabase, Railway Postgres, Render Postgres, or another managed Postgres database.
- GitHub Actions Secrets for database and X/Twitter credentials.
- Public nflverse play-by-play as the current data feed.

## 1. Create Managed Postgres

Create a managed Postgres database and copy its SQLAlchemy URL.

Examples:

```text
postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
```

Use this as the GitHub Secret `DATABASE_URL`.

## 2. Add GitHub Secrets

In GitHub:

```text
Repo -> Settings -> Secrets and variables -> Actions -> New repository secret
```

Required secrets:

```text
DATABASE_URL
X_API_KEY
X_API_SECRET
X_ACCESS_TOKEN
X_ACCESS_TOKEN_SECRET
```

## 3. Add GitHub Variables

In:

```text
Repo -> Settings -> Secrets and variables -> Actions -> Variables
```

Start safely:

```text
TWEETS_ENABLED=false
DRY_RUN=true
```

After validation and a successful dry run:

```text
TWEETS_ENABLED=true
DRY_RUN=false
```

## 4. Backfill The Cloud Database

Kickergami must have historical combos before real posting.

First, use the manual CSV workflow for 1970-1998:

```text
Actions -> Kickergami Backfill -> Run workflow
```

Provide the normalized 1970-1998 historical CSV path, such as:

```text
sample_data/nfl_official_1970_1998_gsis_enhanced_partial.csv
```

Then backfill 1999-present directly from nflverse with no upload:

```text
Actions -> Kickergami nflverse Backfill -> Run workflow
```

Use:

```text
start_season: 1999
end_season: blank
```

The public nflverse feed covers 1999-present play-by-play. The required 1970-1998 history still needs normalized historical CSV data.

## 5. Validate Cloud Posting Readiness

Run:

```text
Actions -> Kickergami Update -> Run workflow
```

With `DRY_RUN=true`, this validates the cloud database, downloads nflverse PBP in the cloud runner, and logs intended tweets without posting.

The workflow runs:

```bash
python scripts/validate_deployment.py --require-cloud
python scripts/run_scheduled_update.py
```

Before enabling real posting, you can temporarily edit the workflow validation command or run this locally against cloud secrets:

```bash
python scripts/validate_deployment.py --require-cloud --require-posting
```

## 6. Scheduled Cloud Runs

The workflow at:

```text
.github/workflows/kickergami-update.yml
```

runs at the NFL end-of-game windows. GitHub schedules are UTC, so the workflow runs both 03:45 UTC and 04:45 UTC on the relevant UTC days to cover Eastern daylight and standard time. The database is idempotent, so duplicate runs are safe.

Mapped windows:

```text
Thursday 11:45 PM ET -> Friday UTC
Saturday 11:45 PM ET -> Sunday UTC
Sunday 11:45 PM ET -> Monday UTC
Monday 11:45 PM ET -> Tuesday UTC
```

With `KICKERGAMI_SKIP_OFFSEASON=true`, cloud runs exit without doing work outside January, February, and September-December.

## 7. Container Option

The repo includes a `Dockerfile` for platforms like Render, Fly.io, Railway, Google Cloud Run Jobs, or AWS ECS scheduled tasks.

Build:

```bash
docker build -t kickergami .
```

Run:

```bash
docker run --env-file .env kickergami
```

For production, store environment variables in the cloud provider's secret manager, not in a committed `.env`.

## Final Cloud Go-Live Checklist

- Managed Postgres exists.
- `DATABASE_URL` GitHub Secret points to managed Postgres, not SQLite.
- X/Twitter secrets are configured.
- Historical backfill has been run into the managed database.
- `Actions -> Kickergami Update -> Run workflow` succeeds in dry-run mode.
- `TWEETS_ENABLED=true`.
- `DRY_RUN=false`.
- Local scheduled tasks are disabled or removed.
