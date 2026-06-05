"""Normalize kicker-game CSV rows into typed records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from app.combo import combo_key

REQUIRED_COLUMNS = {
    "date",
    "season",
    "week",
    "season_type",
    "game_id",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "xp_made",
    "xp_attempts",
    "fg_made",
    "fg_attempts",
    "fg_made_distances",
}


@dataclass(frozen=True)
class KickerGameRecord:
    date: date
    season: int
    week: int
    season_type: str
    game_id: str
    player_id: str
    player_name: str
    team: str
    opponent: str
    xp_made: int
    xp_missed: int
    fg_made: int
    fg_missed: int
    fg_yards_total: int
    combo_key: str


def parse_fg_made_distances(value: object, fg_made: int) -> list[int]:
    if value is None or pd.isna(value) or str(value).strip() == "":
        if fg_made > 0:
            raise ValueError("fg_made_distances is required when fg_made > 0")
        return []

    distances = [int(part.strip()) for part in str(value).split(",") if part.strip()]
    if len(distances) != fg_made:
        raise ValueError(f"fg_made_distances count ({len(distances)}) does not equal fg_made ({fg_made})")
    return distances


def validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")


def normalize_dataframe(df: pd.DataFrame) -> list[KickerGameRecord]:
    validate_columns(df)
    records: list[KickerGameRecord] = []

    for idx, row in df.iterrows():
        season = int(row["season"])
        if season < 1970:
            continue

        xp_made = int(row["xp_made"])
        xp_attempts = int(row["xp_attempts"])
        fg_made = int(row["fg_made"])
        fg_attempts = int(row["fg_attempts"])
        if xp_attempts < xp_made:
            raise ValueError(f"Row {idx}: xp_attempts cannot be less than xp_made")
        if fg_attempts < fg_made:
            raise ValueError(f"Row {idx}: fg_attempts cannot be less than fg_made")

        distances = parse_fg_made_distances(row["fg_made_distances"], fg_made)
        xp_missed = xp_attempts - xp_made
        fg_missed = fg_attempts - fg_made
        fg_yards_total = sum(distances)
        key = combo_key(xp_made, xp_missed, fg_made, fg_missed, fg_yards_total)

        records.append(
            KickerGameRecord(
                date=pd.to_datetime(row["date"]).date(),
                season=season,
                week=int(row["week"]),
                season_type=str(row["season_type"]).strip(),
                game_id=str(row["game_id"]).strip(),
                player_id=str(row["player_id"]).strip(),
                player_name=str(row["player_name"]).strip(),
                team=str(row["team"]).strip(),
                opponent=str(row["opponent"]).strip(),
                xp_made=xp_made,
                xp_missed=xp_missed,
                fg_made=fg_made,
                fg_missed=fg_missed,
                fg_yards_total=fg_yards_total,
                combo_key=key,
            )
        )

    return sorted(records, key=lambda r: (r.date, r.season, r.week, r.game_id, r.player_name))


def normalize_csv(path: str | Path) -> list[KickerGameRecord]:
    return normalize_dataframe(pd.read_csv(path, keep_default_na=False))

