import pandas as pd

from app.data_sources.nflverse_pbp import current_nfl_season, normalize_nflverse_pbp


def test_current_nfl_season_handles_january() -> None:
    assert current_nfl_season(pd.Timestamp("2026-01-10").date()) == 2025


def test_normalize_nflverse_pbp_kicker_lines() -> None:
    df = pd.DataFrame(
        [
            {
                "game_id": "2025_01_DAL_PHI",
                "season": 2025,
                "week": 1,
                "season_type": "REG",
                "game_date": "2025-09-07",
                "posteam": "PHI",
                "defteam": "DAL",
                "play_type": "extra_point",
                "kicker_player_id": "k1",
                "kicker_player_name": "Test Kicker",
                "extra_point_result": "good",
                "field_goal_result": None,
                "kick_distance": None,
                "game_seconds_remaining": 1200,
            },
            {
                "game_id": "2025_01_DAL_PHI",
                "season": 2025,
                "week": 1,
                "season_type": "REG",
                "game_date": "2025-09-07",
                "posteam": "PHI",
                "defteam": "DAL",
                "play_type": "extra_point",
                "kicker_player_id": "k1",
                "kicker_player_name": "Test Kicker",
                "extra_point_result": "failed",
                "field_goal_result": None,
                "kick_distance": None,
                "game_seconds_remaining": 900,
            },
            {
                "game_id": "2025_01_DAL_PHI",
                "season": 2025,
                "week": 1,
                "season_type": "REG",
                "game_date": "2025-09-07",
                "posteam": "PHI",
                "defteam": "DAL",
                "play_type": "field_goal",
                "kicker_player_id": "k1",
                "kicker_player_name": "Test Kicker",
                "extra_point_result": None,
                "field_goal_result": "made",
                "kick_distance": 33,
                "game_seconds_remaining": 600,
            },
            {
                "game_id": "2025_01_DAL_PHI",
                "season": 2025,
                "week": 1,
                "season_type": "REG",
                "game_date": "2025-09-07",
                "posteam": "PHI",
                "defteam": "DAL",
                "play_type": "field_goal",
                "kicker_player_id": "k1",
                "kicker_player_name": "Test Kicker",
                "extra_point_result": None,
                "field_goal_result": "missed",
                "kick_distance": 48,
                "game_seconds_remaining": 300,
            },
            {
                "game_id": "2025_01_DAL_PHI",
                "season": 2025,
                "week": 1,
                "season_type": "REG",
                "game_date": "2025-09-07",
                "posteam": None,
                "defteam": None,
                "play_type": "no_play",
                "kicker_player_id": None,
                "kicker_player_name": None,
                "extra_point_result": None,
                "field_goal_result": None,
                "kick_distance": None,
                "game_seconds_remaining": 0,
            },
        ]
    )

    [record] = normalize_nflverse_pbp(df)
    assert record.xp_made == 1
    assert record.xp_missed == 1
    assert record.fg_made == 1
    assert record.fg_missed == 1
    assert record.fg_yards_total == 33
    assert record.combo_key == "1-1-1-1-33"

