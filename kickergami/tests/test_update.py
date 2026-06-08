from datetime import date

from sqlalchemy import select

from app.config import Settings
from app.models import KickerCombo, KickerGame, TweetLog
from app.normalize import KickerGameRecord
from app.update import process_current_records


class NoopTwitterClient:
    def post(self, text: str) -> None:
        pass


def _settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        data_source="current_csv",
        current_games_csv=None,
        nflverse_season=None,
        nflverse_cache_dir="data/cache/nflverse",
        nflverse_refresh=True,
        nflverse_pbp_url_template="https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz",
        skip_offseason=True,
        x_api_key=None,
        x_api_secret=None,
        x_access_token=None,
        x_access_token_secret=None,
        tweets_enabled=False,
        dry_run=True,
    )


def _record(game_id: str, player_id: str, name: str, combo_key: str) -> KickerGameRecord:
    xp_made, xp_missed, fg_made, fg_missed, fg_yards_total = [int(part) for part in combo_key.split("-")]
    return KickerGameRecord(
        date=date(2026, 9, 20),
        season=2026,
        week=3,
        season_type="REG",
        game_id=game_id,
        player_id=player_id,
        player_name=name,
        team="AAA",
        opponent="BBB",
        xp_made=xp_made,
        xp_missed=xp_missed,
        fg_made=fg_made,
        fg_missed=fg_missed,
        fg_yards_total=fg_yards_total,
        combo_key=combo_key,
    )


def test_update_tracks_new_combo_repeated_within_same_batch(session) -> None:
    records = [
        _record("g1", "p1", "First", "3-0-2-0-77"),
        _record("g2", "p2", "Second", "3-0-2-0-77"),
    ]

    result = process_current_records(session, records, settings=_settings(), twitter_client=NoopTwitterClient())

    assert result.new_kickergamis == 1
    assert result.repeats == 1
    assert session.get(KickerCombo, "3-0-2-0-77").occurrence_count == 2
    assert [game.is_kickergami for game in session.scalars(select(KickerGame).order_by(KickerGame.game_id)).all()] == [True, False]
    assert len(session.scalars(select(TweetLog)).all()) == 1

