"""Backfill Kickergami records from public nflverse PBP, 1999-present."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.backfill import BackfillResult, process_records
from app.data_sources.nflverse_pbp import current_nfl_season, load_current_nflverse_records
from app.db import create_session_factory, init_db


def _merge_results(total: BackfillResult, current: BackfillResult) -> BackfillResult:
    total.inserted_games += current.inserted_games
    total.skipped_games += current.skipped_games
    total.new_combos += current.new_combos
    total.repeats += current.repeats
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=1999)
    parser.add_argument("--end-season", type=int, default=current_nfl_season())
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--cache-dir", default="data/cache/nflverse")
    parser.add_argument("--refresh", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    if args.start_season < 1999:
        raise ValueError("nflverse PBP backfill starts at 1999; use normalized CSV for 1970-1998")
    if args.end_season < args.start_season:
        raise ValueError("--end-season must be greater than or equal to --start-season")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_db(args.database_url)
    session_factory = create_session_factory(args.database_url)
    total = BackfillResult()

    with session_factory() as session:
        for season in range(args.start_season, args.end_season + 1):
            logging.info("Backfilling nflverse season %s", season)
            records = load_current_nflverse_records(
                season=season,
                cache_dir=args.cache_dir,
                refresh=args.refresh,
            )
            result = process_records(session, records)
            _merge_results(total, result)
            logging.info("Season %s result: %s", season, result)

    print(total)


if __name__ == "__main__":
    main()

