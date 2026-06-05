from datetime import date

from scripts.run_scheduled_update import is_nfl_season_window


def test_is_nfl_season_window() -> None:
    assert is_nfl_season_window(date(2026, 1, 15)) is True
    assert is_nfl_season_window(date(2026, 9, 15)) is True
    assert is_nfl_season_window(date(2026, 6, 15)) is False

