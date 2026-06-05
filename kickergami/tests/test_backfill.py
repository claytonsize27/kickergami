from datetime import date

from sqlalchemy import select

from app.backfill import process_records
from app.models import KickerCombo, KickerGame
from app.normalize import KickerGameRecord


def _record(game_id: str, player_id: str, combo: str = "2-0-1-0-33") -> KickerGameRecord:
    xp_made, xp_missed, fg_made, fg_missed, fg_yards_total = [int(part) for part in combo.split("-")]
    return KickerGameRecord(
        date=date(1970, 9, 20),
        season=1970,
        week=1,
        season_type="REG",
        game_id=game_id,
        player_id=player_id,
        player_name=f"Kicker {player_id}",
        team="PHI",
        opponent="DAL",
        xp_made=xp_made,
        xp_missed=xp_missed,
        fg_made=fg_made,
        fg_missed=fg_missed,
        fg_yards_total=fg_yards_total,
        combo_key=combo,
    )


def test_backfill_marks_first_occurrence_as_kickergami(session) -> None:
    process_records(session, [_record("g1", "p1")])
    game = session.scalar(select(KickerGame))
    combo = session.get(KickerCombo, "2-0-1-0-33")
    assert game is not None
    assert game.is_kickergami is True
    assert combo is not None
    assert combo.occurrence_count == 1


def test_backfill_marks_repeat_combo_as_not_kickergami(session) -> None:
    process_records(session, [_record("g1", "p1"), _record("g2", "p2")])
    games = session.scalars(select(KickerGame).order_by(KickerGame.game_id)).all()
    combo = session.get(KickerCombo, "2-0-1-0-33")
    assert [game.is_kickergami for game in games] == [True, False]
    assert combo is not None
    assert combo.occurrence_count == 2


def test_idempotency_prevents_duplicate_kicker_games(session) -> None:
    records = [_record("g1", "p1"), _record("g2", "p2")]
    first = process_records(session, records)
    second = process_records(session, records)
    assert first.inserted_games == 2
    assert second.inserted_games == 0
    assert second.skipped_games == 2
    assert len(session.scalars(select(KickerGame)).all()) == 2
    assert session.get(KickerCombo, "2-0-1-0-33").occurrence_count == 2

