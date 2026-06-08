"""Historical backfill workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KickerCombo, KickerGame
from app.normalize import KickerGameRecord
from app.season_tracker import record_new_kickergami

logger = logging.getLogger(__name__)


@dataclass
class BackfillResult:
    inserted_games: int = 0
    skipped_games: int = 0
    new_combos: int = 0
    repeats: int = 0


def _game_exists(session: Session, record: KickerGameRecord) -> bool:
    return (
        session.scalar(
            select(KickerGame.id).where(
                KickerGame.game_id == record.game_id,
                KickerGame.player_id == record.player_id,
            )
        )
        is not None
    )


def _insert_game(session: Session, record: KickerGameRecord, is_kickergami: bool) -> None:
    session.add(
        KickerGame(
            game_id=record.game_id,
            date=record.date,
            season=record.season,
            week=record.week,
            season_type=record.season_type,
            player_id=record.player_id,
            player_name=record.player_name,
            team=record.team,
            opponent=record.opponent,
            xp_made=record.xp_made,
            xp_missed=record.xp_missed,
            fg_made=record.fg_made,
            fg_missed=record.fg_missed,
            fg_yards_total=record.fg_yards_total,
            combo_key=record.combo_key,
            is_kickergami=is_kickergami,
        )
    )


def _insert_combo(session: Session, record: KickerGameRecord) -> None:
    session.add(
        KickerCombo(
            combo_key=record.combo_key,
            xp_made=record.xp_made,
            xp_missed=record.xp_missed,
            fg_made=record.fg_made,
            fg_missed=record.fg_missed,
            fg_yards_total=record.fg_yards_total,
            first_date=record.date,
            first_season=record.season,
            first_week=record.week,
            first_season_type=record.season_type,
            first_game_id=record.game_id,
            first_player_id=record.player_id,
            first_player_name=record.player_name,
            first_team=record.team,
            occurrence_count=1,
        )
    )


def process_records(session: Session, records: list[KickerGameRecord]) -> BackfillResult:
    result = BackfillResult()
    ordered = sorted(records, key=lambda r: (r.date, r.season, r.week, r.game_id, r.player_name))
    seen_combos = {key for key in session.scalars(select(KickerCombo.combo_key)).all()}

    for record in ordered:
        if _game_exists(session, record):
            result.skipped_games += 1
            continue

        if record.combo_key not in seen_combos:
            _insert_game(session, record, True)
            _insert_combo(session, record)
            seen_combos.add(record.combo_key)
            record_new_kickergami(session, record)
            result.new_combos += 1
        else:
            _insert_game(session, record, False)
            combo = session.get(KickerCombo, record.combo_key)
            if combo is None:
                session.flush()
                combo = session.get(KickerCombo, record.combo_key)
            if combo is None:
                raise RuntimeError(f"Combo was marked seen but not found: {record.combo_key}")
            combo.occurrence_count += 1
            result.repeats += 1
        result.inserted_games += 1

    session.commit()
    logger.info("Backfill result: %s", result)
    return result
