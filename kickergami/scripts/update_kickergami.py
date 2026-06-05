"""Run completed-game Kickergami update from a normalized CSV file."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data_sources.current_csv import load_current_csv
from app.db import create_session_factory, init_db
from app.update import process_current_records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", help="Normalized completed-game CSV path")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    init_db(args.database_url)
    session_factory = create_session_factory(args.database_url)
    with session_factory() as session:
        result = process_current_records(session, load_current_csv(args.csv))
    print(result)


if __name__ == "__main__":
    main()
