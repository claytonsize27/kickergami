"""Historical normalized CSV data source."""

from __future__ import annotations

from pathlib import Path

from app.normalize import KickerGameRecord, normalize_csv


def load_historical_csv(paths: list[str | Path]) -> list[KickerGameRecord]:
    records: list[KickerGameRecord] = []
    for path in paths:
        records.extend(normalize_csv(path))
    return sorted(records, key=lambda r: (r.date, r.season, r.week, r.game_id, r.player_name))

