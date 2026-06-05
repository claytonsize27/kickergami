"""Validate whether Kickergami is ready for unattended production posting."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.config import Settings
from app.db import init_db


def deployment_problems(
    settings: Settings,
    require_cloud: bool = False,
    require_posting: bool = False,
    skip_db: bool = False,
) -> list[str]:
    problems: list[str] = []

    if not skip_db:
        try:
            init_db(settings.database_url)
        except Exception as exc:
            problems.append(f"Database is not reachable/initializable: {exc}")

    if require_cloud:
        if settings.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL must be managed Postgres for cloud production, not SQLite")
        if settings.data_source == "current_csv":
            problems.append("KICKERGAMI_DATA_SOURCE should be nflverse_pbp or another cloud-accessible feed")

    if settings.data_source == "current_csv":
        if not settings.current_games_csv:
            problems.append("KICKERGAMI_CURRENT_CSV is required for current_csv data source")
        elif not Path(settings.current_games_csv).exists():
            problems.append(f"KICKERGAMI_CURRENT_CSV does not exist: {settings.current_games_csv}")
    elif settings.data_source == "nflverse_pbp":
        if "{season}" not in settings.nflverse_pbp_url_template:
            problems.append("KICKERGAMI_NFLVERSE_PBP_URL_TEMPLATE must contain {season}")
    else:
        problems.append(f"Unsupported KICKERGAMI_DATA_SOURCE: {settings.data_source}")

    missing_x = [
        name
        for name, value in {
            "X_API_KEY": settings.x_api_key,
            "X_API_SECRET": settings.x_api_secret,
            "X_ACCESS_TOKEN": settings.x_access_token,
            "X_ACCESS_TOKEN_SECRET": settings.x_access_token_secret,
        }.items()
        if not value
    ]
    if missing_x:
        problems.append(f"Missing X credentials: {', '.join(missing_x)}")

    if require_posting:
        if settings.dry_run:
            problems.append("DRY_RUN must be false for real posting")
        if not settings.tweets_enabled:
            problems.append("TWEETS_ENABLED must be true for real posting")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-posting", action="store_true", help="Fail if real X posting is not enabled")
    parser.add_argument("--require-cloud", action="store_true", help="Fail if configured for local SQLite or local-only data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    problems = deployment_problems(settings, require_cloud=args.require_cloud, require_posting=args.require_posting)

    print("Kickergami deployment validation")
    print(f"database_url: {settings.database_url}")
    print(f"data_source: {settings.data_source}")
    print(f"tweets_enabled: {settings.tweets_enabled}")
    print(f"dry_run: {settings.dry_run}")
    print(f"skip_offseason: {settings.skip_offseason}")

    if problems:
        print("\nNot production-ready:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("\nProduction checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
