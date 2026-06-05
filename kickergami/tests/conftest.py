import pytest

from app.config import Settings
from app.db import make_engine
from app.models import Base
from sqlalchemy.orm import Session


@pytest.fixture
def session():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, future=True) as session:
        yield session


@pytest.fixture
def settings_factory():
    def _make(**overrides):
        values = {
            "database_url": "sqlite:///:memory:",
            "data_source": "current_csv",
            "current_games_csv": "sample_data/current_sample.csv",
            "nflverse_season": None,
            "nflverse_cache_dir": "data/cache/nflverse",
            "nflverse_refresh": True,
            "nflverse_pbp_url_template": "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz",
            "skip_offseason": True,
            "x_api_key": None,
            "x_api_secret": None,
            "x_access_token": None,
            "x_access_token_secret": None,
            "tweets_enabled": False,
            "dry_run": True,
        }
        values.update(overrides)
        return Settings(**values)

    return _make
