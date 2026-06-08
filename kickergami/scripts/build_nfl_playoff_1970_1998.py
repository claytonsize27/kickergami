"""Build a normalized 1970-1998 NFL playoff kicker-game CSV.

Counts come from official NFL.com player postseason game logs. Made field-goal
distances for multi-FG rows come from NFL-branded annual scoring-summary PDFs
already cached by the regular-season backfill.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from collections import Counter, defaultdict
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).resolve().parent.parent))
import build_nfl_official_1970_1998 as nfl_logs
import complete_nfl_annual_summary_distances as annual
import complete_nfl_gsis_distances as gsis


BASE_DIR = Path("sample_data")
REGULAR_IN = BASE_DIR / "nfl_official_1970_1998_gsis_enhanced_partial.csv"
PLAYOFF_OUT = BASE_DIR / "nfl_official_1970_1998_playoffs.csv"
UNRESOLVED_OUT = BASE_DIR / "nfl_official_1970_1998_playoffs_unresolved.csv"
CACHE_DIR = BASE_DIR / ".nfl_playoff_logs"

CSV_COLUMNS = nfl_logs.CSV_COLUMNS
UNRESOLVED_COLUMNS = CSV_COLUMNS[:-1] + ["long_made_fg", "source_url", "reason"]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Kickergami official postseason backfill"})

annual.ANNUAL_SUMMARY_URLS[1998] = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151440/1998.pdf"

VERIFIED_OVERRIDES: dict[tuple[str, str], tuple[list[int], dict[str, str]]] = {
    ("1970_POST_03_SB_BAL_DAL", "nfl-mike-clark"): ([14, 30], {}),
    ("1970_POST_03_SB_BAL_DAL", "nfl-mike-clark-2"): ([14, 30], {}),
    ("1976_POST_03_SB_DET_MIN", "nfl-errol-mann"): (
        [24, 40],
        {"game_id": "1976_POST_03_SB_OAK_MIN", "team": "OAK", "opponent": "MIN"},
    ),
    ("1976_POST_03_SB_OAK_MIN", "nfl-errol-mann"): ([24, 40], {}),
    ("1979_POST_01_WC_CHI_PHI", "nfl-tony-franklin-2"): ([29, 34], {}),
    ("1979_POST_01_WC_DEN_HOU", "nfl-toni-fritsch"): ([31, 20], {}),
    ("1979_POST_03_CONF_HOU_PIT", "nfl-toni-fritsch"): ([21, 23], {}),
    ("1979_POST_03_CONF_LA_TB", "nfl-frank-corral"): ([19, 21, 23], {}),
    ("1984_POST_01_WC_LA_SEA", "nfl-norm-johnson"): ([35, 44], {}),
    ("1986_POST_02_DIV_NYJ_WAS", "nfl-mark-moseley"): (
        [38, 22, 27],
        {"game_id": "1986_POST_02_DIV_NYJ_CLE", "team": "CLE", "opponent": "NYJ"},
    ),
    ("1986_POST_03_CONF_DEN_WAS", "nfl-mark-moseley"): (
        [29, 24],
        {"game_id": "1986_POST_03_CONF_DEN_CLE", "team": "CLE", "opponent": "DEN"},
    ),
    ("1991_POST_01_WC_ATL_NO", "nfl-morten-andersen"): ([45, 35], {}),
    ("1991_POST_01_WC_ATL_NO", "nfl-norm-johnson"): ([44, 36], {}),
    ("1991_POST_01_WC_LA_KC", "nfl-jeff-jaeger"): ([32, 26], {}),
    ("1991_POST_01_WC_DAL_CHI", "nfl-kevin-butler"): ([19, 43], {}),
    ("1991_POST_02_DIV_DAL_DET", "nfl-ken-willis"): ([28, 28], {}),
    ("1991_POST_02_DIV_HOU_DEN", "nfl-david-treadwell"): ([49, 28], {}),
    ("1991_POST_02_DIV_KC_BUF", "nfl-scott-norwood"): ([33, 20, 47], {}),
    ("1998_POST_02_DIV_ARI_MIN", "nfl-gary-anderson"): ([34, 20], {}),
}

FULL_SCAN_SEASONS = {1970, 1975, 1976, 1991}
SUPPLEMENTAL_PLAYERS = [
    nfl_logs.PlayerSeason(name="George Blanda", slug="george-blanda", season=1970, team="OAK"),
    nfl_logs.PlayerSeason(name="Jim O'Brien", slug="jim-o-brien", season=1970, team="BAL"),
    nfl_logs.PlayerSeason(name="Errol Mann", slug="errol-mann", season=1976, team="OAK"),
]
EXCLUDED_GAME_IDS = {
    "1976_POST_01_DIV_NE_DET",
    "1976_POST_02_CONF_PIT_DET",
    "1979_POST_02_DIV_HOU_STL",
    "1991_POST_01_WC_NYG_HOU",
}
SUPPLEMENTAL_ROWS = [
    {
        "date": "1970-12-26",
        "season": 1970,
        "week": 1,
        "season_type": "POST",
        "game_id": "1970_POST_01_DIV_CIN_BAL",
        "player_id": "nfl-jim-o-brien",
        "player_name": "Jim O'Brien",
        "team": "BAL",
        "opponent": "CIN",
        "xp_made": 2,
        "xp_attempts": 2,
        "fg_made": 1,
        "fg_attempts": 1,
        "fg_made_distances": "44",
    },
    {
        "date": "1970-12-27",
        "season": 1970,
        "week": 1,
        "season_type": "POST",
        "game_id": "1970_POST_01_DIV_MIA_OAK",
        "player_id": "nfl-george-blanda",
        "player_name": "George Blanda",
        "team": "OAK",
        "opponent": "MIA",
        "xp_made": 3,
        "xp_attempts": 3,
        "fg_made": 0,
        "fg_attempts": 0,
        "fg_made_distances": "",
    },
    {
        "date": "1971-01-03",
        "season": 1970,
        "week": 2,
        "season_type": "POST",
        "game_id": "1970_POST_02_CONF_OAK_BAL",
        "player_id": "nfl-george-blanda",
        "player_name": "George Blanda",
        "team": "OAK",
        "opponent": "BAL",
        "xp_made": 2,
        "xp_attempts": 2,
        "fg_made": 1,
        "fg_attempts": 1,
        "fg_made_distances": "48",
    },
    {
        "date": "1971-01-03",
        "season": 1970,
        "week": 2,
        "season_type": "POST",
        "game_id": "1970_POST_02_CONF_OAK_BAL",
        "player_id": "nfl-jim-o-brien",
        "player_name": "Jim O'Brien",
        "team": "BAL",
        "opponent": "OAK",
        "xp_made": 3,
        "xp_attempts": 3,
        "fg_made": 2,
        "fg_attempts": 2,
        "fg_made_distances": "16,23",
    },
    {
        "date": "1971-01-17",
        "season": 1970,
        "week": 3,
        "season_type": "POST",
        "game_id": "1970_POST_03_SB_BAL_DAL",
        "player_id": "nfl-jim-o-brien",
        "player_name": "Jim O'Brien",
        "team": "BAL",
        "opponent": "DAL",
        "xp_made": 1,
        "xp_attempts": 2,
        "fg_made": 1,
        "fg_attempts": 1,
        "fg_made_distances": "32",
    },
]

FG_LINE_RE = re.compile(
    r"^\s*([A-Za-z. ]{2,14})\s*\S+\s*FG\s+"
    r"([A-Za-z.'?\u2019\-]+(?:\s+[A-Za-z.'?\u2019\-]+){0,2})\s+(\d{1,2})\b",
    re.I | re.M,
)
COMPACT_FG_LINE_RE = re.compile(
    r"^\s*([A-Za-z. ]{2,14})\s*\S+\s*FG\s+([A-Za-z.'?\u2019\-]{3,})(\d{1,2})\b",
    re.I | re.M,
)
GAME_HEADER_RE = re.compile(
    r"^(?P<stage>(?:AFC|NFC)\s+(?:WILD CARD|FIRST[- ]ROUND|SECOND[- ]ROUND|DIVISIONAL|CHAMPIONSHIP)(?:\s+(?:PLAYOFFS?|GAME))?|SUPER BOWL[^\n]*)\s*$",
    re.I | re.M,
)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["date"], int(r["week"]), r["game_id"], r["player_name"])))


def dedupe_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    deduped: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        deduped[(str(row["game_id"]), str(row["player_id"]))] = row
    return list(deduped.values())


def player_slug(player_id: str) -> str:
    return player_id.removeprefix("nfl-")


def regular_player_seasons() -> list[nfl_logs.PlayerSeason]:
    by_key: dict[tuple[int, str], Counter[str]] = defaultdict(Counter)
    names: dict[tuple[int, str], str] = {}
    for row in read_rows(REGULAR_IN):
        season = int(row["season"])
        if 1970 <= season <= 1998:
            slug = player_slug(row["player_id"])
            key = (season, slug)
            by_key[key][row["team"]] += 1
            names[key] = row["player_name"]

    players: list[nfl_logs.PlayerSeason] = []
    seen_players: set[tuple[int, str, str]] = set()
    for (season, slug), teams in sorted(by_key.items()):
        team = teams.most_common(1)[0][0]
        player = nfl_logs.PlayerSeason(name=names[(season, slug)], slug=slug, season=season, team=team)
        players.append(player)
        seen_players.add((player.season, player.slug, player.team))
    for player in SUPPLEMENTAL_PLAYERS:
        if (player.season, player.slug, player.team) not in seen_players:
            players.append(player)
    return players


def get(url: str) -> str:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    time.sleep(0.02)
    return response.text


def cached_player_log(player: nfl_logs.PlayerSeason) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{player.season}_{player.slug}.html"
    if path.exists():
        return path.read_text(encoding="utf-8")
    html = get(f"{nfl_logs.BASE}/players/{player.slug}/stats/logs/{player.season}/")
    path.write_text(html, encoding="utf-8")
    return html


def int_cell(value: object) -> int:
    if pd.isna(value) or str(value).strip() in {"", "--", "nan"}:
        return 0
    return int(float(str(value).strip()))


def playoff_game_id(season: int, week: int, team: str, opponent: str, away: bool) -> str:
    away_team, home_team = (team, opponent) if away else (opponent, team)
    stage = playoff_stage(season, week)
    return f"{season}_POST_{week:02d}_{stage}_{away_team}_{home_team}"


def playoff_stage(season: int, week: int) -> str:
    if season <= 1977:
        return {1: "DIV", 2: "CONF", 3: "SB"}.get(week, f"W{week:02d}")
    if season == 1982:
        return {1: "R1", 2: "R2", 3: "CONF", 4: "SB"}.get(week, f"W{week:02d}")
    return {1: "WC", 2: "DIV", 3: "CONF", 4: "SB", 5: "SB"}.get(week, f"W{week:02d}")


def log_postseason_rows(player: nfl_logs.PlayerSeason) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    url = f"{nfl_logs.BASE}/players/{player.slug}/stats/logs/{player.season}/"
    try:
        html = cached_player_log(player)
        tables = pd.read_html(StringIO(html))
    except Exception:
        return [], []
    if len(tables) < 2:
        return [], []

    df = tables[1]
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
        opponent = nfl_logs.normalize_team(raw_opp.removeprefix("@"), player.season)
        week = int_cell(row["WK"])
        date = pd.to_datetime(str(row["Game Date"]).strip()).date().isoformat()
        base = {
            "date": date,
            "season": player.season,
            "week": week,
            "season_type": "POST",
            "game_id": playoff_game_id(player.season, week, player.team, opponent, away),
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
                    "reason": "NFL.com postseason game log does not list every made FG distance",
                }
            )
    return exact, review


def game_teams(game_id: str) -> tuple[str, str]:
    parts = game_id.split("_")
    return parts[-2], parts[-1]


def date_label(row: dict[str, object]) -> str:
    played = pd.to_datetime(row["date"]).date()
    return f"{played.strftime('%B')} {played.day}".upper()


def stage_label(row: dict[str, object]) -> str:
    stage = str(row["game_id"]).split("_")[4]
    return {
        "WC": "WILD CARD",
        "R1": "FIRST",
        "R2": "SECOND",
        "DIV": "DIVISIONAL",
        "CONF": "CHAMPIONSHIP",
        "SB": "SUPER BOWL",
    }.get(stage, stage)


def postseason_blocks(summary: annual.AnnualSummary) -> list[str]:
    matches = list(GAME_HEADER_RE.finditer(summary.text))
    blocks: list[str] = []
    for index, match in enumerate(matches):
        if match.start() < 1000:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(summary.text)
        block = summary.text[match.start() : end]
        if not re.search(
            r"\b(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),\s+"
            r"(?:December|January)\s+\d{1,2}\b",
            block[:800],
            re.I,
        ):
            continue
        if "FG" in block or "kick" in block.lower():
            blocks.append(block)
    return blocks


def postseason_teams(summary: annual.AnnualSummary) -> set[str]:
    teams: set[str] = set()
    upper_text = summary.text.upper()
    start = upper_text.find("WILD CARD QUALIFIER")
    if start == -1:
        start = upper_text.find("AFC WILD CARD")
    if start == -1:
        start = upper_text.find("AFC DIVISIONAL")
    end = upper_text.find("WEEK ONE", start)
    if start != -1 and end != -1:
        playoff_index = upper_text[start:end]
        for team, aliases in annual.TEAM_NAME_ALIASES.items():
            if any(alias.upper() in playoff_index for alias in aliases):
                teams.add(team)
    for block in postseason_blocks(summary):
        head = block[:700].upper()
        for team, aliases in annual.TEAM_NAME_ALIASES.items():
            if any(alias.upper() in head for alias in aliases):
                teams.add(team)
    return teams


def block_matches_row(block: str, row: dict[str, object]) -> bool:
    upper = block.upper()
    away, home = game_teams(str(row["game_id"]))
    if date_label(row) not in upper:
        return False
    if stage_label(row) not in upper:
        return False
    hits = 0
    for team in (away, home):
        if any(alias.upper() in upper for alias in annual.TEAM_NAME_ALIASES.get(team, [team])):
            hits += 1
    return hits == 2


def team_for_prefix(prefix: str, game_id: str) -> str | None:
    away, home = game_teams(game_id)
    clean = annual.norm(prefix)
    matches: list[str] = []
    for team in (away, home):
        if any(annual.norm(alias) == clean for alias in annual.TEAM_PREFIX_ALIASES.get(team, [])):
            matches.append(team)
    return matches[0] if len(matches) == 1 else None


def source_last_name(name: str) -> str:
    parts = [part for part in re.split(r"\s+", name.strip()) if part]
    return annual.norm(parts[-1]) if parts else ""


def extract_fg_events(block: str, game_id: str) -> list[tuple[str, str, int]]:
    events: list[tuple[str, str, int]] = []
    for pattern in (FG_LINE_RE, COMPACT_FG_LINE_RE):
        for match in pattern.finditer(block):
            team = team_for_prefix(match.group(1), game_id)
            if team:
                events.append((team, source_last_name(match.group(2)), int(match.group(3))))
    return events


def annual_distances(row: dict[str, object], summary: annual.AnnualSummary, blocks: list[str]) -> tuple[list[int], str]:
    matches = [block for block in blocks if block_matches_row(block, row)]
    if not matches:
        return [], "no matching NFL annual postseason scoring block found"
    if len(matches) > 1:
        return [], f"ambiguous NFL annual postseason scoring block count {len(matches)}"

    events = extract_fg_events(matches[0], str(row["game_id"]))
    distances = [
        yards
        for team, kicker, yards in events
        if team == row["team"] and annual.kicker_matches(kicker, str(row["player_name"]))
    ]
    expected_count = int(row["fg_made"])
    expected_long = int(row["long_made_fg"])
    if len(distances) != expected_count:
        same_team = [(kicker, yards) for team, kicker, yards in events if team == row["team"]]
        return distances, f"NFL annual postseason distance parse mismatch: got {distances}, expected count {expected_count}; same-team events {same_team}"
    if expected_long not in distances:
        return distances, f"NFL annual postseason long-FG mismatch: got {distances}, expected long {expected_long}"
    return distances, ""


def main() -> None:
    exact_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    seen_rows: set[tuple[str, str]] = set()
    postseason_team_cache: dict[int, set[str]] = {}

    for player in regular_player_seasons():
        if player.season not in postseason_team_cache:
            summary = annual.source_text(player.season)
            postseason_team_cache[player.season] = postseason_teams(summary) if summary else set()
        if player.season not in FULL_SCAN_SEASONS and player.team not in postseason_team_cache[player.season]:
            continue
        exact, review = log_postseason_rows(player)
        for row in exact + review:
            if row["game_id"] in EXCLUDED_GAME_IDS:
                continue
            key = (str(row["game_id"]), str(row["player_id"]))
            if key in seen_rows:
                continue
            seen_rows.add(key)
            if row in exact:
                exact_rows.append(row)
            else:
                review_rows.append(row)

    summaries: dict[int, annual.AnnualSummary] = {}
    summary_blocks: dict[int, list[str]] = {}
    resolved_multi: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []

    for row in review_rows:
        override = VERIFIED_OVERRIDES.get((str(row["game_id"]), str(row["player_id"])))
        if override:
            distances, corrections = override
            resolved_multi.append({**row, **corrections, "fg_made_distances": ",".join(map(str, distances))})
            continue
        season = int(row["season"])
        if season not in summaries:
            summary = annual.source_text(season)
            if summary is not None:
                summaries[season] = summary
                summary_blocks[season] = postseason_blocks(summary)
        summary = summaries.get(season)
        if not summary:
            unresolved.append({**row, "reason": "NFL annual scoring summary unavailable"})
            continue
        distances, reason = annual_distances(row, summary, summary_blocks[season])
        if reason:
            unresolved.append({**row, "fg_made_distances": ",".join(map(str, distances)), "reason": reason})
            continue
        resolved_multi.append({**row, "fg_made_distances": ",".join(map(str, distances))})

    upload_rows = exact_rows + resolved_multi
    upload_keys = {(str(row["game_id"]), str(row["player_id"])) for row in upload_rows}
    for row in SUPPLEMENTAL_ROWS:
        key = (str(row["game_id"]), str(row["player_id"]))
        if key not in upload_keys:
            upload_rows.append(row)
            upload_keys.add(key)
    upload_rows = dedupe_rows(upload_rows)
    write_csv(PLAYOFF_OUT, CSV_COLUMNS, upload_rows)
    write_csv(UNRESOLVED_OUT, UNRESOLVED_COLUMNS, unresolved)

    print(f"playoff rows written: {len(upload_rows)}")
    print(f"playoff multi-FG rows resolved: {len(resolved_multi)}")
    print(f"playoff unresolved rows: {len(unresolved)}")

    # Validate with the app's normal importer.
    from app.normalize import normalize_csv

    print(f"normalized playoff records: {len(normalize_csv(PLAYOFF_OUT))}")


if __name__ == "__main__":
    main()
