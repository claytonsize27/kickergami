"""Print a season-level Kickergami summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db import create_session_factory
from app.models import KickerCombo, KickerGame, SeasonTracker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("season", type=int)
    parser.add_argument("--season-type", default=None)
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()

    session_factory = create_session_factory(args.database_url)
    with session_factory() as session:
        tracker_query = select(SeasonTracker).where(SeasonTracker.season == args.season)
        if args.season_type:
            tracker_query = tracker_query.where(SeasonTracker.season_type == args.season_type)
        trackers = session.scalars(tracker_query).all()

        total = sum(item.kickergami_count for item in trackers)
        latest = max((item.last_kickergami_combo_key for item in trackers if item.last_kickergami_combo_key), default="none")
        print(f"season: {args.season}")
        print(f"total Kickergamis: {total}")
        print(f"latest Kickergami: {latest}")

        recent = session.scalars(
            select(KickerGame)
            .where(KickerGame.season == args.season, KickerGame.is_kickergami.is_(True))
            .order_by(KickerGame.date.desc(), KickerGame.id.desc())
            .limit(10)
        ).all()
        print("\ntop 10 most recent Kickergamis")
        for game in recent:
            print(f"{game.date} {game.player_name} {game.team} {game.combo_key}")

        rarest = session.scalars(select(KickerCombo).order_by(KickerCombo.occurrence_count.asc(), KickerCombo.first_date.desc()).limit(10)).all()
        print("\ntop 10 rarest combos by occurrence_count")
        for combo in rarest:
            print(f"{combo.combo_key} {combo.occurrence_count}x first={combo.first_date} {combo.first_player_name} ({combo.first_team})")


if __name__ == "__main__":
    main()
