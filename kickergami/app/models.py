"""SQLAlchemy ORM models for Kickergami."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class KickerGame(Base):
    __tablename__ = "kicker_games"
    __table_args__ = (UniqueConstraint("game_id", "player_id", name="uq_kicker_game_player"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(100), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    season: Mapped[int] = mapped_column(Integer, index=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    season_type: Mapped[str] = mapped_column(String(20), index=True)
    player_id: Mapped[str] = mapped_column(String(100), index=True)
    player_name: Mapped[str] = mapped_column(String(200))
    team: Mapped[str] = mapped_column(String(10))
    opponent: Mapped[str] = mapped_column(String(10))
    xp_made: Mapped[int] = mapped_column(Integer)
    xp_missed: Mapped[int] = mapped_column(Integer)
    fg_made: Mapped[int] = mapped_column(Integer)
    fg_missed: Mapped[int] = mapped_column(Integer)
    fg_yards_total: Mapped[int] = mapped_column(Integer)
    combo_key: Mapped[str] = mapped_column(String(50), index=True)
    is_kickergami: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KickerCombo(Base):
    __tablename__ = "kicker_combos"

    combo_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    xp_made: Mapped[int] = mapped_column(Integer)
    xp_missed: Mapped[int] = mapped_column(Integer)
    fg_made: Mapped[int] = mapped_column(Integer)
    fg_missed: Mapped[int] = mapped_column(Integer)
    fg_yards_total: Mapped[int] = mapped_column(Integer)
    first_date: Mapped[date] = mapped_column(Date)
    first_season: Mapped[int] = mapped_column(Integer)
    first_week: Mapped[int] = mapped_column(Integer)
    first_season_type: Mapped[str] = mapped_column(String(20))
    first_game_id: Mapped[str] = mapped_column(String(100))
    first_player_id: Mapped[str] = mapped_column(String(100))
    first_player_name: Mapped[str] = mapped_column(String(200))
    first_team: Mapped[str] = mapped_column(String(10))
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TweetLog(Base):
    __tablename__ = "tweet_log"
    __table_args__ = (UniqueConstraint("game_id", "player_id", "combo_key", "tweet_type", name="uq_tweet_once"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[str] = mapped_column(String(100), index=True)
    player_id: Mapped[str] = mapped_column(String(100), index=True)
    combo_key: Mapped[str] = mapped_column(String(50), index=True)
    tweet_type: Mapped[str] = mapped_column(String(50), index=True)
    tweet_text: Mapped[str] = mapped_column(String(280))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SeasonTracker(Base):
    __tablename__ = "season_tracker"

    season: Mapped[int] = mapped_column(Integer, primary_key=True)
    season_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    kickergami_count: Mapped[int] = mapped_column(Integer, default=0)
    last_kickergami_combo_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_kickergami_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

