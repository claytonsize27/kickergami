"""Completed-game normalized CSV data source."""

from __future__ import annotations

from pathlib import Path

from app.normalize import KickerGameRecord, normalize_csv


def load_current_csv(path: str | Path) -> list[KickerGameRecord]:
    return normalize_csv(path)

