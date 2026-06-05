"""Scheduled completed-game update entrypoint.

This is the command cron, Task Scheduler, or Codex automation should run at
the end-of-game windows. It reads its completed-games CSV path from
KICKERGAMI_CURRENT_CSV.
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.data_sources.current_csv import load_current_csv
from app.data_sources.nflverse_pbp import load_current_nflverse_records
from app.db import create_session_factory, init_db
from app.update import process_current_records


def is_nfl_season_window(today: date | None = None) -> bool:
    today = today or date.today()
    return today.month in {1, 2, 9, 10, 11, 12}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    if settings.skip_offseason and not is_nfl_season_window():
        logging.info("Skipping scheduled update outside NFL season window")
        return 0

    if settings.data_source == "nflverse_pbp":
        records = load_current_nflverse_records(
            season=settings.nflverse_season,
            cache_dir=settings.nflverse_cache_dir,
            url_template=settings.nflverse_pbp_url_template,
            refresh=settings.nflverse_refresh,
        )
    elif settings.data_source == "current_csv":
        if not settings.current_games_csv:
            logging.error("KICKERGAMI_CURRENT_CSV is not set")
            return 2
        csv_path = Path(settings.current_games_csv)
        if not csv_path.exists():
            logging.error("Completed-games CSV does not exist: %s", csv_path)
            return 2
        records = load_current_csv(csv_path)
    else:
        logging.error("Unsupported KICKERGAMI_DATA_SOURCE: %s", settings.data_source)
        return 2

    init_db(settings.database_url)
    session_factory = create_session_factory(settings.database_url)
    with session_factory() as session:
        result = process_current_records(session, records, settings=settings)
    logging.info("Scheduled update complete: %s", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
