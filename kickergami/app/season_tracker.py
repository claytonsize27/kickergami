"""Season tracker maintenance."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import SeasonTracker
from app.normalize import KickerGameRecord


def record_new_kickergami(session: Session, record: KickerGameRecord) -> SeasonTracker:
    tracker = session.get(SeasonTracker, {"season": record.season, "season_type": record.season_type})
    if tracker is None:
        tracker = SeasonTracker(
            season=record.season,
            season_type=record.season_type,
            kickergami_count=0,
        )
        session.add(tracker)
        session.flush()

    tracker.kickergami_count += 1
    tracker.last_kickergami_combo_key = record.combo_key
    tracker.last_kickergami_date = record.date
    return tracker

