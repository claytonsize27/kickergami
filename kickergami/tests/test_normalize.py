import pandas as pd
import pytest

from app.normalize import normalize_dataframe, parse_fg_made_distances


def _df(**overrides):
    data = {
        "date": ["2026-09-13"],
        "season": [2026],
        "week": [1],
        "season_type": ["REG"],
        "game_id": ["2026_01_DAL_PHI"],
        "player_id": ["k1"],
        "player_name": ["Test Kicker"],
        "team": ["PHI"],
        "opponent": ["DAL"],
        "xp_made": [3],
        "xp_attempts": [4],
        "fg_made": [2],
        "fg_attempts": [3],
        "fg_made_distances": ["33,45"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_parse_fg_made_distances() -> None:
    assert parse_fg_made_distances("33,45,51", 3) == [33, 45, 51]


def test_validation_error_when_fg_made_count_mismatch() -> None:
    with pytest.raises(ValueError, match="does not equal fg_made"):
        parse_fg_made_distances("33,45", 3)


def test_validation_error_when_fg_made_has_blank_distances() -> None:
    with pytest.raises(ValueError, match="required"):
        parse_fg_made_distances("", 1)


def test_normalization_of_misses() -> None:
    [record] = normalize_dataframe(_df())
    assert record.xp_missed == 1
    assert record.fg_missed == 1
    assert record.fg_yards_total == 78
    assert record.combo_key == "3-1-2-1-78"


def test_filters_pre_1970_rows() -> None:
    assert normalize_dataframe(_df(season=[1969])) == []

