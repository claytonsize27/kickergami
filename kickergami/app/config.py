"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: str | Path = ".env") -> None:
    """Load simple KEY=VALUE entries without overriding existing env vars."""
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    data_source: str
    current_games_csv: str | None
    nflverse_season: int | None
    nflverse_cache_dir: str
    nflverse_refresh: bool
    nflverse_pbp_url_template: str
    skip_offseason: bool
    x_api_key: str | None
    x_api_secret: str | None
    x_access_token: str | None
    x_access_token_secret: str | None
    tweets_enabled: bool
    dry_run: bool


def get_settings() -> Settings:
    load_env_file()
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///kickergami.db"),
        data_source=os.getenv("KICKERGAMI_DATA_SOURCE", "current_csv"),
        current_games_csv=os.getenv("KICKERGAMI_CURRENT_CSV"),
        nflverse_season=int(os.getenv("KICKERGAMI_NFLVERSE_SEASON")) if os.getenv("KICKERGAMI_NFLVERSE_SEASON") else None,
        nflverse_cache_dir=os.getenv("KICKERGAMI_NFLVERSE_CACHE_DIR", "data/cache/nflverse"),
        nflverse_refresh=_env_bool("KICKERGAMI_NFLVERSE_REFRESH", True),
        nflverse_pbp_url_template=os.getenv(
            "KICKERGAMI_NFLVERSE_PBP_URL_TEMPLATE",
            "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz",
        ),
        skip_offseason=_env_bool("KICKERGAMI_SKIP_OFFSEASON", True),
        x_api_key=os.getenv("X_API_KEY"),
        x_api_secret=os.getenv("X_API_SECRET"),
        x_access_token=os.getenv("X_ACCESS_TOKEN"),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        tweets_enabled=_env_bool("TWEETS_ENABLED", False),
        dry_run=_env_bool("DRY_RUN", True),
    )
