"""Resolve remaining kicker distances from official NFL.com Game Center PDFs."""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent))
import complete_nfl_gsis_distances as gsis


BASE_DIR = Path("sample_data")
UNRESOLVED_IN = BASE_DIR / "nfl_gsis_unresolved_multi_fg_rows.csv"
UPLOAD_IN = BASE_DIR / "nfl_official_1970_1998_upload.csv"
FINAL_OUT = BASE_DIR / "nfl_official_1970_1998_gsis_enhanced_partial.csv"
RESOLVED_OUT = BASE_DIR / "nfl_gsis_resolved_multi_fg_rows.csv"
UNRESOLVED_OUT = BASE_DIR / "nfl_gsis_unresolved_multi_fg_rows.csv"
CACHE_DIR = BASE_DIR / ".nfl_gamecenter_gamebooks"

TEAM_SLUGS = {
    "ARI": "cardinals",
    "ATL": "falcons",
    "BAL": "ravens",
    "BUF": "bills",
    "CAR": "panthers",
    "CHI": "bears",
    "CIN": "bengals",
    "CLE": "browns",
    "DAL": "cowboys",
    "DEN": "broncos",
    "DET": "lions",
    "GB": "packers",
    "IND": "colts",
    "JAX": "jaguars",
    "KC": "chiefs",
    "LA": "rams",
    "MIA": "dolphins",
    "MIN": "vikings",
    "NE": "patriots",
    "NO": "saints",
    "NYG": "giants",
    "NYJ": "jets",
    "OAK": "raiders",
    "PHI": "eagles",
    "PIT": "steelers",
    "SD": "chargers",
    "SEA": "seahawks",
    "SF": "49ers",
    "STL": "rams",
    "TB": "buccaneers",
    "TEN": "oilers",
    "HOU": "oilers",
    "WAS": "redskins",
}


SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def slug_for_game(game_id: str) -> str | None:
    season_s, week_s, away, home = game_id.split("_", 3)
    away_slug = TEAM_SLUGS.get(away)
    home_slug = TEAM_SLUGS.get(home)
    if not away_slug or not home_slug:
        return None
    return f"{away_slug}-at-{home_slug}-{season_s}-reg-{int(week_s)}"


def gamecenter_pdf_url(game_id: str) -> str | None:
    cache_path = CACHE_DIR / f"{game_id}.url"
    if cache_path.exists():
        text = cache_path.read_text(encoding="utf-8").strip()
        return text or None

    slug = slug_for_game(game_id)
    if not slug:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("", encoding="utf-8")
        return None
    page_url = f"https://www.nfl.com/games/{slug}"
    response = SESSION.get(page_url, timeout=30)
    if response.status_code != 200:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("", encoding="utf-8")
        return None
    body = html.unescape(response.text)
    matches = re.findall(r"https://static\.www\.nfl\.com/image/upload/[^\"'<> ]+?/gamecenter/[^\"'<> ]+?\.pdf", body)
    if not matches:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("", encoding="utf-8")
        return None
    url = matches[0]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(url, encoding="utf-8")
    return url


def fetch_pdf_candidate(game_id: str, rows: list[dict[str, str]]) -> gsis.Candidate | None:
    url = gamecenter_pdf_url(game_id)
    if not url:
        return None
    season = int(rows[0]["season"])
    week = int(rows[0]["week"])
    cache_path = CACHE_DIR / f"{game_id}.pdf"
    if cache_path.exists():
        content = cache_path.read_bytes()
    else:
        response = SESSION.get(url, timeout=30)
        if response.status_code != 200 or not response.content.startswith(b"%PDF"):
            return None
        content = response.content
        cache_path.write_bytes(content)
    text = gsis.pdf_text(content)
    if len(text.strip()) < 100:
        return None
    return gsis.Candidate(season=season, week=week, gsis_id=0, url=url, text=text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=1995)
    parser.add_argument("--end-season", type=int, default=1998)
    parser.add_argument("--limit-games", type=int, default=0)
    args = parser.parse_args()

    upload_rows = read_rows(UPLOAD_IN)
    resolved = read_rows(RESOLVED_OUT)
    unresolved = read_rows(UNRESOLVED_OUT)
    resolved_keys = {(row["game_id"], row["player_id"]) for row in resolved}
    current_unresolved = [
        row
        for row in unresolved
        if not (args.start_season <= int(row["season"]) <= args.end_season)
    ]
    retry_rows = [
        row
        for row in unresolved
        if args.start_season <= int(row["season"]) <= args.end_season
        and (row["game_id"], row["player_id"]) not in resolved_keys
    ]
    by_game: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in retry_rows:
        by_game[row["game_id"]].append(row)

    for idx, (game_id, rows) in enumerate(sorted(by_game.items()), start=1):
        if args.limit_games and idx > args.limit_games:
            break
        candidate = fetch_pdf_candidate(game_id, rows)
        if not candidate or not gsis.text_matches_game(candidate.text, rows):
            current_unresolved.extend({**row, "unresolved_reason": "no matching NFL.com Game Center gamebook found"} for row in rows)
            gsis.print_progress(game_id, resolved, current_unresolved)
            gsis.flush_outputs(upload_rows, resolved, current_unresolved)
            continue
        distances_by_name = gsis.distances_for_rows(candidate, rows)
        for row in rows:
            fg_made = int(row["fg_made"])
            distances = gsis.clean_distances(gsis.distances_for_player(distances_by_name, row["player_name"]), fg_made)
            if len(distances) == fg_made:
                out = {col: row[col] for col in gsis.CSV_COLUMNS if col != "fg_made_distances"}
                out["fg_made_distances"] = ",".join(str(d) for d in distances)
                out["gsis_url"] = candidate.url
                resolved.append(out)
            else:
                current_unresolved.append(
                    {
                        **row,
                        "gsis_url": candidate.url,
                        "unresolved_reason": f"NFL.com Game Center distance parse mismatch: got {distances}, expected count {fg_made}",
                    }
                )
        gsis.print_progress(game_id, resolved, current_unresolved)
        gsis.flush_outputs(upload_rows, resolved, current_unresolved)

    gsis.flush_outputs(upload_rows, resolved, current_unresolved)
    print(f"resolved multi-FG rows: {len(resolved)}")
    print(f"unresolved multi-FG rows: {len(current_unresolved)}")


if __name__ == "__main__":
    main()
