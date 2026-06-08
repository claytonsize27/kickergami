from datetime import date

from sqlalchemy import select

from app.backfill import process_records
from app.models import KickerCombo, KickerGame
from app.normalize import KickerGameRecord


def _record(game_id: str, player_id: str, player_name: str, combo_key: str) -> KickerGameRecord:
    xp_made, xp_missed, fg_made, fg_missed, fg_yards_total = [int(part) for part in combo_key.split("-")]
    return KickerGameRecord(
        date=date(1970, 9, 20),
        season=1970,
        week=1,
        season_type="REG",
        game_id=game_id,
        player_id=player_id,
        player_name=player_name,
        team="AAA",
        opponent="BBB",
        xp_made=xp_made,
        xp_missed=xp_missed,
        fg_made=fg_made,
        fg_missed=fg_missed,
        fg_yards_total=fg_yards_total,
        combo_key=combo_key,
    )


def test_backfill_tracks_repeated_combos_within_same_batch(session) -> None:
    records = [
        _record("g1", "p1", "One", "1-0-1-0-33"),
        _record("g2", "p2", "Two", "2-0-1-0-44"),
        _record("g3", "p3", "Three", "1-0-1-0-33"),
    ]

    result = process_records(session, records)

    assert result.new_combos == 2
    assert result.repeats == 1
    assert session.get(KickerCombo, "1-0-1-0-33").occurrence_count == 2
    assert len(session.scalars(select(KickerGame)).all()) == 3

