"""Closest-prior-line rarity helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.combo import Combo
from app.models import KickerCombo


@dataclass(frozen=True)
class ClosestPriorCombo:
    combo_key: str
    xp_made: int
    xp_missed: int
    fg_made: int
    fg_missed: int
    fg_yards_total: int
    first_player_name: str
    first_team: str
    first_date: date
    occurrence_count: int
    distance: int


def distance_score(new_combo: Combo, prior_combo: KickerCombo | Combo) -> int:
    return (
        abs(new_combo.xp_made - prior_combo.xp_made) * 10
        + abs(new_combo.xp_missed - prior_combo.xp_missed) * 15
        + abs(new_combo.fg_made - prior_combo.fg_made) * 10
        + abs(new_combo.fg_missed - prior_combo.fg_missed) * 15
        + abs(new_combo.fg_yards_total - prior_combo.fg_yards_total)
    )


def find_closest_prior_combo(session: Session, new_combo: Combo) -> ClosestPriorCombo | None:
    combos = session.scalars(select(KickerCombo)).all()
    if not combos:
        return None

    best = min(combos, key=lambda combo: (distance_score(new_combo, combo), combo.first_date, combo.combo_key))
    return ClosestPriorCombo(
        combo_key=best.combo_key,
        xp_made=best.xp_made,
        xp_missed=best.xp_missed,
        fg_made=best.fg_made,
        fg_missed=best.fg_missed,
        fg_yards_total=best.fg_yards_total,
        first_player_name=best.first_player_name,
        first_team=best.first_team,
        first_date=best.first_date,
        occurrence_count=best.occurrence_count,
        distance=distance_score(new_combo, best),
    )

