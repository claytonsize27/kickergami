import os

from app.config import load_env_file
from scripts.validate_deployment import deployment_problems


def test_load_env_file_does_not_override_existing_env(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DRY_RUN=false\nKICKERGAMI_CURRENT_CSV=data.csv\n", encoding="utf-8")
    monkeypatch.setenv("DRY_RUN", "true")

    load_env_file(env_file)

    assert os.environ["DRY_RUN"] == "true"
    assert os.environ["KICKERGAMI_CURRENT_CSV"] == "data.csv"


def test_require_cloud_rejects_sqlite(settings_factory) -> None:
    settings = settings_factory(database_url="sqlite:///kickergami.db", data_source="nflverse_pbp")
    problems = deployment_problems(settings, require_cloud=True, require_posting=False, skip_db=True)
    assert any("managed Postgres" in problem for problem in problems)


def test_require_cloud_rejects_local_current_csv(settings_factory) -> None:
    settings = settings_factory(
        database_url="postgresql+psycopg2://user:pass@example.com:5432/kickergami",
        data_source="current_csv",
    )
    problems = deployment_problems(settings, require_cloud=True, require_posting=False, skip_db=True)
    assert any("cloud-accessible feed" in problem for problem in problems)
