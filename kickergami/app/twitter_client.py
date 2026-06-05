"""Tweet generation and optional X posting."""

from __future__ import annotations

import logging
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import TweetLog
from app.normalize import KickerGameRecord
from app.rarity import ClosestPriorCombo

logger = logging.getLogger(__name__)


def _print_intended_tweet(text: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(text)


def _base_tweet(record: KickerGameRecord) -> str:
    xp_total = record.xp_made + record.xp_missed
    fg_total = record.fg_made + record.fg_missed
    return (
        "🏈 KICKERGAMI!\n\n"
        f"{record.player_name} ({record.team})\n\n"
        f"XP: {record.xp_made}/{xp_total}\n\n"
        f"FG: {record.fg_made}/{fg_total}\n\n"
        f"{record.fg_yards_total} FG Yards\n\n"
        "First occurrence of:\n\n"
        f"({record.xp_made},{record.xp_missed},{record.fg_made},{record.fg_missed},{record.fg_yards_total})\n\n"
        "Regular season + playoffs\n"
        "1970-present\n\n"
        "#Kickergami"
    )


def build_tweet_text(
    record: KickerGameRecord,
    closest_prior: ClosestPriorCombo | None = None,
    season_kickergami_count: int | None = None,
) -> str:
    tweet = _base_tweet(record)

    if closest_prior is not None:
        closest = (
            "\n\nClosest prior:\n"
            f"({closest_prior.xp_made},{closest_prior.xp_missed},{closest_prior.fg_made},"
            f"{closest_prior.fg_missed},{closest_prior.fg_yards_total})\n"
            f"First: {closest_prior.first_player_name} ({closest_prior.first_team}), {closest_prior.first_date}\n"
            f"Seen {closest_prior.occurrence_count}x"
        )
        if len(tweet + closest) <= 280:
            tweet += closest

    if season_kickergami_count is not None:
        season = f"\n\n{record.season} Kickergamis: {season_kickergami_count}"
        if len(tweet + season) <= 280:
            tweet += season

    return tweet[:280]


def tweet_type_for_settings(settings: Settings) -> str:
    if settings.dry_run:
        return "dry_run_new_kickergami"
    if not settings.tweets_enabled:
        return "new_kickergami_disabled"
    return "new_kickergami"


class TwitterClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def post(self, text: str) -> None:
        if self.settings.dry_run or not self.settings.tweets_enabled:
            _print_intended_tweet(text)
            return
        try:
            import tweepy
        except ImportError as exc:
            raise RuntimeError("tweepy is required for real X/Twitter posting") from exc

        required = [
            self.settings.x_api_key,
            self.settings.x_api_secret,
            self.settings.x_access_token,
            self.settings.x_access_token_secret,
        ]
        if not all(required):
            raise RuntimeError("Missing X/Twitter credentials")

        client = tweepy.Client(
            consumer_key=self.settings.x_api_key,
            consumer_secret=self.settings.x_api_secret,
            access_token=self.settings.x_access_token,
            access_token_secret=self.settings.x_access_token_secret,
        )
        client.create_tweet(text=text)
        logger.info("Posted Kickergami tweet")


def save_tweet_once(session: Session, record: KickerGameRecord, tweet_type: str, tweet_text: str) -> bool:
    existing = session.scalar(
        select(TweetLog).where(
            TweetLog.game_id == record.game_id,
            TweetLog.player_id == record.player_id,
            TweetLog.combo_key == record.combo_key,
            TweetLog.tweet_type == tweet_type,
        )
    )
    if existing is not None:
        return False
    session.add(
        TweetLog(
            game_id=record.game_id,
            player_id=record.player_id,
            combo_key=record.combo_key,
            tweet_type=tweet_type,
            tweet_text=tweet_text,
        )
    )
    return True
