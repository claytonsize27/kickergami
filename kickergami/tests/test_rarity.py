from datetime import date

from app.combo import Combo
from app.models import KickerCombo
from app.rarity import distance_score, find_closest_prior_combo


def test_distance_scoring_for_closest_prior_line() -> None:
    new = Combo(3, 0, 4, 1, 177)
    prior = Combo(2, 1, 3, 0, 170)
    assert distance_score(new, prior) == 57


def test_find_closest_prior_combo(session) -> None:
    session.add_all(
        [
            KickerCombo(
                combo_key="1-0-1-0-30",
                xp_made=1,
                xp_missed=0,
                fg_made=1,
                fg_missed=0,
                fg_yards_total=30,
                first_date=date(1970, 9, 20),
                first_season=1970,
                first_week=1,
                first_season_type="REG",
                first_game_id="g1",
                first_player_id="p1",
                first_player_name="A Kicker",
                first_team="AAA",
                occurrence_count=2,
            ),
            KickerCombo(
                combo_key="3-0-4-1-176",
                xp_made=3,
                xp_missed=0,
                fg_made=4,
                fg_missed=1,
                fg_yards_total=176,
                first_date=date(2000, 1, 1),
                first_season=1999,
                first_week=18,
                first_season_type="POST",
                first_game_id="g2",
                first_player_id="p2",
                first_player_name="B Kicker",
                first_team="BBB",
                occurrence_count=1,
            ),
        ]
    )
    session.commit()

    closest = find_closest_prior_combo(session, Combo(3, 0, 4, 1, 177))
    assert closest is not None
    assert closest.combo_key == "3-0-4-1-176"
    assert closest.distance == 1

