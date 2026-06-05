from datetime import date

from app.normalize import KickerGameRecord
from app.twitter_client import build_tweet_text


def test_tweet_generation_stays_under_280_chars() -> None:
    record = KickerGameRecord(
        date=date(2026, 9, 13),
        season=2026,
        week=1,
        season_type="REG",
        game_id="g1",
        player_id="p1",
        player_name="A Very Reasonable Kicker Name",
        team="PHI",
        opponent="DAL",
        xp_made=3,
        xp_missed=0,
        fg_made=4,
        fg_missed=1,
        fg_yards_total=177,
        combo_key="3-0-4-1-177",
    )
    assert len(build_tweet_text(record, season_kickergami_count=12)) <= 280

