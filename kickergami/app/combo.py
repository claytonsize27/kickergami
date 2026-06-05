"""Combo key and tuple utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Combo:
    xp_made: int
    xp_missed: int
    fg_made: int
    fg_missed: int
    fg_yards_total: int

    @property
    def key(self) -> str:
        return combo_key(self.xp_made, self.xp_missed, self.fg_made, self.fg_missed, self.fg_yards_total)


def combo_key(xp_made: int, xp_missed: int, fg_made: int, fg_missed: int, fg_yards_total: int) -> str:
    return f"{xp_made}-{xp_missed}-{fg_made}-{fg_missed}-{fg_yards_total}"


def combo_from_key(key: str) -> Combo:
    parts = [int(part) for part in key.split("-")]
    if len(parts) != 5:
        raise ValueError(f"Invalid combo_key: {key}")
    return Combo(*parts)

