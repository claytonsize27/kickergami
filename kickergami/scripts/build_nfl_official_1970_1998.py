"""Build conservative NFL.com-sourced kicker-game CSVs for 1970-1998.

NFL.com game logs expose every kicker-game's FGM/FGA/XPM/XPA and longest made
field goal. They do not expose every made field-goal distance for multi-FG
games, so only rows with 0 or 1 made FG can be made upload-safe from logs alone.
Rows with 2+ made FGs are written to a review file for gamebook completion.
"""

from __future__ import annotations

import csv
import argparse
import re
import time
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup


START_SEASON = 1970
END_SEASON = 1998
BASE = "https://www.nfl.com"
OUT_DIR = Path("sample_data")
EXACT_OUT = OUT_DIR / "nfl_official_1970_1998_exact_from_logs.csv"
REVIEW_OUT = OUT_DIR / "nfl_official_1970_1998_needs_gamebook_distances.csv"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Kickergami official-source backfill"})
TEAM_CACHE: dict[tuple[str, int], str | None] = {}

CSV_COLUMNS = [
    "date",
    "season",
    "week",
    "season_type",
    "game_id",
    "player_id",
    "player_name",
    "team",
    "opponent",
    "xp_made",
    "xp_attempts",
    "fg_made",
    "fg_attempts",
    "fg_made_distances",
]

REVIEW_COLUMNS = CSV_COLUMNS[:-1] + ["long_made_fg", "source_url", "reason"]

TEAM_ABBR = {
    "49ers": "SF",
    "Bears": "CHI",
    "Bengals": "CIN",
    "Bills": "BUF",
    "Broncos": "DEN",
    "Browns": "CLE",
    "Buccaneers": "TB",
    "Chiefs": "KC",
    "Cowboys": "DAL",
    "Dolphins": "MIA",
    "Eagles": "PHI",
    "Falcons": "ATL",
    "Giants": "NYG",
    "Jaguars": "JAX",
    "Jets": "NYJ",
    "Lions": "DET",
    "Packers": "GB",
    "Panthers": "CAR",
    "Patriots": "NE",
    "Ravens": "BAL",
    "Redskins": "WAS",
    "Commanders": "WAS",
    "Saints": "NO",
    "Seahawks": "SEA",
    "Steelers": "PIT",
    "Vikings": "MIN",
}


@dataclass(frozen=True)
class PlayerSeason:
    name: str
    slug: str
    season: int
    team: str


def get(url: str) -> str:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.03)
    return response.text


def historical_franchise_abbr(nickname: str, season: int) -> str | None:
    if nickname == "Cardinals":
        return "STL" if season <= 1987 else "PHX" if season <= 1993 else "ARI"
    if nickname == "Chargers":
        return "SD"
    if nickname == "Colts":
        return "BAL" if season <= 1983 else "IND"
    if nickname in {"Oilers", "Titans"}:
        return "HOU" if season <= 1996 else "TEN"
    if nickname == "Raiders":
        return "OAK" if season <= 1981 or season >= 1995 else "LA"
    if nickname == "Rams":
        return "LA" if season <= 1994 else "STL"
    return None


def normalize_team(value: str, season: int) -> str:
    value = value.strip()
    if value in TEAM_ABBR.values():
        return value
    for key, abbr in TEAM_ABBR.items():
        if value.endswith(key):
            return abbr
    for key in ["Cardinals", "Chargers", "Colts", "Oilers", "Titans", "Raiders", "Rams"]:
        if value.endswith(key):
            abbr = historical_franchise_abbr(key, season)
            if abbr:
                return abbr
    raise ValueError(f"Unknown NFL team name: {value!r}")


def player_slug_from_href(href: str) -> str:
    match = re.search(r"/players/([^/]+)/", href)
    if not match:
        raise ValueError(f"Cannot parse player slug from {href!r}")
    return match.group(1)


def player_seasons_from_stats_page(season: int) -> Iterable[PlayerSeason]:
    url = f"{BASE}/stats/player-stats/category/field-goals/{season}/REG/all/kickingfgmade/desc"
    while url:
        soup = BeautifulSoup(get(url), "html.parser")
        for link in soup.select("a.d3-o-player-fullname[href*='/players/']"):
            name = link.get_text(" ", strip=True)
            slug = player_slug_from_href(link["href"])
            team = team_for_player_season(slug, season)
            if team:
                yield PlayerSeason(name=name, slug=slug, season=season, team=team)

        next_link = soup.select_one("a.nfl-o-table-pagination__next[href]")
        url = BASE + next_link["href"] if next_link else ""


def team_for_player_season(slug: str, season: int) -> str | None:
    key = (slug, season)
    if key in TEAM_CACHE:
        return TEAM_CACHE[key]
    soup = BeautifulSoup(get(f"{BASE}/players/{slug}/stats/"), "html.parser")
    text = soup.get_text("\n", strip=True)
    pattern = re.compile(rf"^{season}\s*\n([^\n]+)$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        TEAM_CACHE[key] = None
        return None
    TEAM_CACHE[key] = normalize_team(match.group(1), season)
    return TEAM_CACHE[key]


def int_cell(value: object) -> int:
    if pd.isna(value) or str(value).strip() in {"", "--"}:
        return 0
    return int(float(str(value).strip()))


def game_id(season: int, week: int, team: str, opponent: str, away: bool) -> str:
    away_team, home_team = (team, opponent) if away else (opponent, team)
    return f"{season}_{week:02d}_{away_team}_{home_team}"


def log_rows(player: PlayerSeason) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    url = f"{BASE}/players/{player.slug}/stats/logs/{player.season}/"
    tables = pd.read_html(StringIO(get(url)))
    if not tables:
        return [], []
    df = tables[0]
    exact: list[dict[str, object]] = []
    review: list[dict[str, object]] = []
    for _, row in df.iterrows():
        fg_made = int_cell(row.get("FGM"))
        fg_attempts = int_cell(row.get("FG ATT"))
        xp_made = int_cell(row.get("XPM"))
        xp_attempts = int_cell(row.get("XP Att"))
        if fg_attempts == 0 and xp_attempts == 0:
            continue

        raw_opp = str(row["OPP"]).strip()
        away = raw_opp.startswith("@")
        opponent = normalize_team(raw_opp.removeprefix("@"), player.season)
        week = int_cell(row["WK"])
        raw_date = str(row["Game Date"]).strip()
        date = pd.to_datetime(raw_date if raw_date.count("/") == 2 else f"{raw_date}/{player.season}").date().isoformat()
        base = {
            "date": date,
            "season": player.season,
            "week": week,
            "season_type": "REG",
            "game_id": game_id(player.season, week, player.team, opponent, away),
            "player_id": f"nfl-{player.slug.strip('-')}",
            "player_name": player.name,
            "team": player.team,
            "opponent": opponent,
            "xp_made": xp_made,
            "xp_attempts": xp_attempts,
            "fg_made": fg_made,
            "fg_attempts": fg_attempts,
        }
        if fg_made <= 1:
            base["fg_made_distances"] = "" if fg_made == 0 else str(int_cell(row.get("Lng")))
            exact.append(base)
        else:
            review.append(
                {
                    **base,
                    "long_made_fg": int_cell(row.get("Lng")),
                    "source_url": url,
                    "reason": "NFL.com game log does not list every made FG distance for multi-FG games",
                }
            )
    return exact, review


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["date"], r["game_id"], r["player_name"])))


def read_existing(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=START_SEASON)
    parser.add_argument("--end-season", type=int, default=END_SEASON)
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    exact_rows: list[dict[str, object]] = read_existing(EXACT_OUT) if args.append else []
    review_rows: list[dict[str, object]] = read_existing(REVIEW_OUT) if args.append else []
    seen: set[tuple[int, str]] = set()
    for season in range(args.start_season, args.end_season + 1):
        for player in player_seasons_from_stats_page(season):
            key = (season, player.slug)
            if key in seen:
                continue
            seen.add(key)
            exact, review = log_rows(player)
            exact_rows.extend(exact)
            review_rows.extend(review)
            print(season, player.name, len(exact), len(review), flush=True)

        write_csv(EXACT_OUT, CSV_COLUMNS, exact_rows)
        write_csv(REVIEW_OUT, REVIEW_COLUMNS, review_rows)
        print(f"wrote through {season}: exact={len(exact_rows)} review={len(review_rows)}", flush=True)

    write_csv(EXACT_OUT, CSV_COLUMNS, exact_rows)
    write_csv(REVIEW_OUT, REVIEW_COLUMNS, review_rows)
    print(f"exact rows: {len(exact_rows)} -> {EXACT_OUT}")
    print(f"needs gamebook rows: {len(review_rows)} -> {REVIEW_OUT}")


if __name__ == "__main__":
    main()
