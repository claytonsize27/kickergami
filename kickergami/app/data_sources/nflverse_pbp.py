"""nflverse/nflfastR play-by-play ingestion.

The public nflverse data release provides season-level play-by-play CSV files.
This adapter turns those rows into Kickergami kicker-game records for completed
games. It is intended for 1999-present data; 1970-1998 still needs the required
normalized historical CSV import path.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd

from app.combo import combo_key
from app.normalize import KickerGameRecord

logger = logging.getLogger(__name__)

DEFAULT_PBP_URL_TEMPLATE = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz"


def current_nfl_season(today: date | None = None) -> int:
    today = today or date.today()
    return today.year - 1 if today.month <= 2 else today.year


def load_nflverse_pbp_csv(
    season: int,
    cache_dir: str | Path | None = None,
    url_template: str = DEFAULT_PBP_URL_TEMPLATE,
    refresh: bool = False,
) -> pd.DataFrame:
    """Load an nflverse play-by-play CSV, optionally caching it locally."""
    if cache_dir is None:
        url = url_template.format(season=season)
        logger.info("Loading nflverse PBP from %s", url)
        return pd.read_csv(url, compression="infer", low_memory=False)

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    destination = cache_path / f"play_by_play_{season}.csv.gz"
    if refresh or not destination.exists():
        url = url_template.format(season=season)
        logger.info("Downloading nflverse PBP from %s to %s", url, destination)
        df = pd.read_csv(url, compression="infer", low_memory=False)
        df.to_csv(destination, index=False, compression="gzip")
        return df

    logger.info("Loading cached nflverse PBP from %s", destination)
    return pd.read_csv(destination, compression="gzip", low_memory=False)


def load_current_nflverse_records(
    season: int | None = None,
    cache_dir: str | Path | None = "data/cache/nflverse",
    url_template: str = DEFAULT_PBP_URL_TEMPLATE,
    refresh: bool = True,
) -> list[KickerGameRecord]:
    season = season or current_nfl_season()
    df = load_nflverse_pbp_csv(season, cache_dir=cache_dir, url_template=url_template, refresh=refresh)
    return normalize_nflverse_pbp(df)


def normalize_nflverse_pbp(df: pd.DataFrame) -> list[KickerGameRecord]:
    required = {"game_id", "season", "week", "season_type", "game_date", "posteam", "defteam", "play_type"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing nflverse PBP columns: {', '.join(sorted(missing))}")

    kicker_id_col = _first_existing_column(df, ["kicker_player_id", "fantasy_player_id"])
    kicker_name_col = _first_existing_column(df, ["kicker_player_name", "player_name", "fantasy_player_name"])
    if kicker_id_col is None or kicker_name_col is None:
        raise ValueError("nflverse PBP must include kicker_player_id/name or equivalent player columns")

    kicking_plays = df[df["play_type"].isin(["field_goal", "extra_point"])].copy()
    kicking_plays = kicking_plays[kicking_plays[kicker_id_col].notna() & (kicking_plays[kicker_id_col].astype(str).str.strip() != "")]
    if kicking_plays.empty:
        return []

    completed_game_ids = _completed_game_ids(df)
    if completed_game_ids:
        kicking_plays = kicking_plays[kicking_plays["game_id"].isin(completed_game_ids)]

    records: list[KickerGameRecord] = []
    group_cols = ["game_id", kicker_id_col]
    for (game_id, player_id), group in kicking_plays.groupby(group_cols, dropna=False):
        first = group.iloc[0]
        field_goals = group[group["play_type"] == "field_goal"]
        extra_points = group[group["play_type"] == "extra_point"]

        fg_made_rows = field_goals[_normalized_result(field_goals.get("field_goal_result")) == "made"]
        fg_attempts = len(field_goals[field_goals.get("field_goal_result", pd.Series(index=field_goals.index)).notna()])
        fg_made = len(fg_made_rows)
        fg_distances = _made_fg_distances(fg_made_rows)

        xp_results = _normalized_result(extra_points.get("extra_point_result"))
        xp_attempts = len(extra_points[xp_results.notna()])
        xp_made = int((xp_results == "good").sum())

        xp_missed = xp_attempts - xp_made
        fg_missed = fg_attempts - fg_made
        fg_yards_total = sum(fg_distances)
        key = combo_key(xp_made, xp_missed, fg_made, fg_missed, fg_yards_total)

        records.append(
            KickerGameRecord(
                date=pd.to_datetime(first["game_date"]).date(),
                season=int(first["season"]),
                week=int(first["week"]),
                season_type=str(first["season_type"]),
                game_id=str(game_id),
                player_id=str(player_id),
                player_name=str(first[kicker_name_col]),
                team=str(first["posteam"]),
                opponent=str(first["defteam"]),
                xp_made=xp_made,
                xp_missed=xp_missed,
                fg_made=fg_made,
                fg_missed=fg_missed,
                fg_yards_total=fg_yards_total,
                combo_key=key,
            )
        )

    return sorted(records, key=lambda r: (r.date, r.season, r.week, r.game_id, r.player_name))


def _first_existing_column(df: pd.DataFrame, names: list[str]) -> str | None:
    return next((name for name in names if name in df.columns), None)


def _normalized_result(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series(dtype="object")
    return series.astype("string").str.lower().str.strip().replace({"nan": pd.NA, "": pd.NA})


def _made_fg_distances(fg_made_rows: pd.DataFrame) -> list[int]:
    if fg_made_rows.empty:
        return []
    if "kick_distance" not in fg_made_rows.columns:
        raise ValueError("nflverse PBP made field goals require kick_distance")

    distances: list[int] = []
    for _, row in fg_made_rows.iterrows():
        value = row["kick_distance"]
        if pd.isna(value):
            raise ValueError(f"Missing kick_distance for made FG in game {row['game_id']}")
        distances.append(int(value))
    return distances


def _completed_game_ids(df: pd.DataFrame) -> set[str]:
    if "game_seconds_remaining" in df.columns:
        remaining = pd.to_numeric(df["game_seconds_remaining"], errors="coerce")
        completed = df[remaining <= 0]["game_id"].dropna().astype(str)
        if not completed.empty:
            return set(completed)

    if "desc" in df.columns:
        desc = df["desc"].astype("string").str.upper()
        completed = df[desc.str.contains("END GAME|END OF GAME", na=False)]["game_id"].dropna().astype(str)
        if not completed.empty:
            return set(completed)

    logger.warning("Could not identify completed games from nflverse PBP; processing all available games")
    return set()

