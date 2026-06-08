"""Completed-game update workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.backfill import _game_exists, _insert_combo, _insert_game
from app.combo import Combo
from app.config import Settings, get_settings
from app.models import KickerCombo
from app.normalize import KickerGameRecord
from app.rarity import find_closest_prior_combo
from app.season_tracker import record_new_kickergami
from app.twitter_client import TwitterClient, build_tweet_text, save_tweet_once, tweet_type_for_settings

logger = logging.getLogger(__name__)


@dataclass
class UpdateResult:
    inserted_games: int = 0
    skipped_games: int = 0
    new_kickergamis: int = 0
    repeats: int = 0
    tweets_logged: int = 0
    tweets_posted: int = 0


def process_current_records(
    session: Session,
    records: list[KickerGameRecord],
    settings: Settings | None = None,
    twitter_client: TwitterClient | None = None,
) -> UpdateResult:
    settings = settings or get_settings()
    twitter_client = twitter_client or TwitterClient(settings)
    result = UpdateResult()
    seen_combos = {key for key in session.scalars(select(KickerCombo.combo_key)).all()}

    for record in sorted(records, key=lambda r: (r.date, r.season, r.week, r.game_id, r.player_name)):
        if _game_exists(session, record):
            result.skipped_games += 1
            continue

        if record.combo_key in seen_combos:
            _insert_game(session, record, False)
            combo = session.get(KickerCombo, record.combo_key)
            if combo is None:
                session.flush()
                combo = session.get(KickerCombo, record.combo_key)
            if combo is None:
                raise RuntimeError(f"Combo was marked seen but not found: {record.combo_key}")
            combo.occurrence_count += 1
            result.inserted_games += 1
            result.repeats += 1
            continue

        closest = find_closest_prior_combo(
            session,
            Combo(record.xp_made, record.xp_missed, record.fg_made, record.fg_missed, record.fg_yards_total),
        )
        _insert_game(session, record, True)
        _insert_combo(session, record)
        seen_combos.add(record.combo_key)
        tracker = record_new_kickergami(session, record)
        tweet_text = build_tweet_text(record, closest, tracker.kickergami_count)
        tweet_type = tweet_type_for_settings(settings)
        if save_tweet_once(session, record, tweet_type, tweet_text):
            result.tweets_logged += 1
            twitter_client.post(tweet_text)
            if tweet_type == "new_kickergami":
                result.tweets_posted += 1
        result.inserted_games += 1
        result.new_kickergamis += 1

    session.commit()
    logger.info("Update result: %s", result)
    return result
