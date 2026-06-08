"""Resolve kicker distances from official NFL annual scoring-summary PDFs.

The PDFs are NFL-branded annual scoring summaries hosted by the Eagles media
CDN. They list every scoring play for each game, including made field-goal
distances in lines such as "Dal - FG Septien 29".
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
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
CACHE_DIR = BASE_DIR / ".nfl_annual_summaries"

ANNUAL_SUMMARY_URLS = {
    1970: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145216/1970.pdf",
    1971: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145600/1971.pdf",
    1972: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145652/1972.pdf",
    1973: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145729/1973.pdf",
    1974: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145810/1974.pdf",
    1975: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145853/1975.pdf",
    1976: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150027/1976.pdf",
    1977: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150108/1977.pdf",
    1978: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150149/1978.pdf",
    1979: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150229/1979.pdf",
    1980: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150309/1980.pdf",
    1981: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150347/1981.pdf",
    1982: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150423/1982.pdf",
    1983: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150505/1983.pdf",
    1984: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150546/1984.pdf",
    1985: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150628/1985.pdf",
    1986: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150709/1986.pdf",
    1987: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150746/1987.pdf",
    1988: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150831/1988.pdf",
    1989: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150907/1989.pdf",
    1990: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150948/1990.pdf",
    1991: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151026/1991.pdf",
    1992: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151103/1992.pdf",
    1993: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151144/1993.pdf",
    1994: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151222/1994.pdf",
    1995: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151420/1995.pdf",
    1996: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151433/1996.pdf",
    1997: "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151436/1997.pdf",
}

TEAM_NAME_ALIASES = {
    "ARI": ["ARIZONA CARDINALS", "ARIZONA", "CARDINALS"],
    "ATL": ["ATLANTA FALCONS", "ATLANTA", "FALCONS"],
    "BAL": ["BALTIMORE COLTS", "BALTIMORE RAVENS", "BALTIMORE", "COLTS", "RAVENS"],
    "BUF": ["BUFFALO BILLS", "BUFFALO", "BILLS"],
    "CAR": ["CAROLINA PANTHERS", "CAROLINA", "PANTHERS"],
    "CHI": ["CHICAGO BEARS", "CHICAGO", "BEARS"],
    "CIN": ["CINCINNATI BENGALS", "CINCINNATI", "BENGALS"],
    "CLE": ["CLEVELAND BROWNS", "CLEVELAND", "BROWNS"],
    "DAL": ["DALLAS COWBOYS", "DALLAS", "COWBOYS"],
    "DEN": ["DENVER BRONCOS", "DENVER", "BRONCOS"],
    "DET": ["DETROIT LIONS", "DETROIT", "LIONS"],
    "GB": ["GREEN BAY PACKERS", "GREEN BAY", "PACKERS"],
    "HOU": ["HOUSTON OILERS", "HOUSTON", "OILERS"],
    "IND": ["INDIANAPOLIS COLTS", "INDIANAPOLIS", "COLTS"],
    "JAX": ["JACKSONVILLE JAGUARS", "JACKSONVILLE", "JAGUARS"],
    "KC": ["KANSAS CITY CHIEFS", "KANSAS CITY", "CHIEFS"],
    "LA": ["LOS ANGELES RAMS", "LOS ANGELES RAIDERS", "LOS ANGELES", "RAMS", "RAIDERS"],
    "MIA": ["MIAMI DOLPHINS", "MIAMI", "DOLPHINS"],
    "MIN": ["MINNESOTA VIKINGS", "MINNESOTA", "VIKINGS"],
    "NE": ["NEW ENGLAND PATRIOTS", "NEW ENGLAND", "BOSTON PATRIOTS", "BOSTON", "PATRIOTS"],
    "NO": ["NEW ORLEANS SAINTS", "NEW ORLEANS", "SAINTS"],
    "NYG": ["NEW YORK GIANTS", "GIANTS"],
    "NYJ": ["NEW YORK JETS", "JETS"],
    "OAK": ["OAKLAND RAIDERS", "OAKLAND", "LOS ANGELES RAIDERS", "RAIDERS"],
    "PHI": ["PHILADELPHIA EAGLES", "PHILADELPHIA", "EAGLES"],
    "PHX": ["PHOENIX CARDINALS", "PHOENIX", "CARDINALS"],
    "PIT": ["PITTSBURGH STEELERS", "PITTSBURGH", "STEELERS"],
    "SD": ["SAN DIEGO CHARGERS", "SAN DIEGO", "CHARGERS"],
    "SEA": ["SEATTLE SEAHAWKS", "SEATTLE", "SEAHAWKS"],
    "SF": ["SAN FRANCISCO 49ERS", "SAN FRANCISCO", "49ERS"],
    "STL": ["ST. LOUIS CARDINALS", "ST. LOUIS RAMS", "ST. LOUIS", "CARDINALS", "RAMS"],
    "TB": ["TAMPA BAY BUCCANEERS", "TAMPA BAY", "BUCCANEERS"],
    "TEN": ["TENNESSEE OILERS", "TENNESSEE", "OILERS"],
    "WAS": ["WASHINGTON REDSKINS", "WASHINGTON", "REDSKINS"],
}

TEAM_PREFIX_ALIASES = {
    "ARI": ["Ariz", "Ari", "Cards", "StL", "St.L", "Phil-Pitt"],
    "ATL": ["Atl"],
    "BAL": ["Balt", "Bal"],
    "BUF": ["Buff"],
    "CAR": ["Car"],
    "CHI": ["Chi"],
    "CIN": ["Cin"],
    "CLE": ["Cle", "Clev", "Cleve"],
    "DAL": ["Dal", "Dall"],
    "DEN": ["Denv", "Den"],
    "DET": ["Det"],
    "GB": ["GB", "G.B."],
    "HOU": ["Hou", "Hous"],
    "IND": ["Ind"],
    "JAX": ["Jax"],
    "KC": ["KC", "K.C."],
    "LA": ["LA", "L.A.", "Rams", "Raiders"],
    "MIA": ["Mia"],
    "MIN": ["Minn", "Min"],
    "NE": ["NE", "N.E.", "Bos", "Bost"],
    "NO": ["NO", "N.O."],
    "NYG": ["NYG", "N.Y.G."],
    "NYJ": ["NYJ", "N.Y.J."],
    "OAK": ["Oak", "LA", "L.A."],
    "PHI": ["Phil", "Phila", "Phi"],
    "PHX": ["Pho", "Phx", "Ariz"],
    "PIT": ["Pitt", "Pit"],
    "SD": ["SD", "S.D."],
    "SEA": ["Sea"],
    "SF": ["SF", "S.F."],
    "STL": ["StL", "St.L", "St.L.", "St. L"],
    "TB": ["TB", "T.B."],
    "TEN": ["Tenn"],
    "WAS": ["Wash", "Was"],
}

DATE_RE = re.compile(
    r"(?=^(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),\s+"
    r"(?:September|October|November|December|January)\s+\d{1,2}\b)",
    re.M,
)
FG_RE = re.compile(
    r"\b([A-Za-z. ]{2,12})\s*[-–—]\s*FG\s+"
    r"([A-Za-z.'?\u2019\-]+(?:\s+[A-Za-z.'?\u2019\-]+){0,2})\s+(\d{1,2})\b",
    re.I,
)
REVERSE_FG_RE = re.compile(
    r"\b([A-Za-z. ]{2,12})\s*[-–—]\s*"
    r"([A-Za-z.'?\u2019\-]+(?:\s+[A-Za-z.'?\u2019\-]+){0,2})\s+FG\s+(\d{1,2})\b",
    re.I,
)
OCR_COMPACT_FG_RE = re.compile(
    r"\b([A-Za-z. ]{2,12})\s*[-–—]\s*FG\s+([A-Za-z.'\-]{3,})(\d{1,2})\b",
    re.I,
)


@dataclass(frozen=True)
class AnnualSummary:
    season: int
    url: str
    text: str
    blocks: list[str]


SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Kickergami official-source annual summary backfill"})


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def source_text(season: int) -> AnnualSummary | None:
    url = ANNUAL_SUMMARY_URLS.get(season)
    if not url:
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = CACHE_DIR / f"{season}.pdf"
    txt_path = CACHE_DIR / f"{season}.txt"
    if not pdf_path.exists():
        response = SESSION.get(url, timeout=45)
        if response.status_code != 200 or not response.content.startswith(b"%PDF"):
            return None
        pdf_path.write_bytes(response.content)
    if txt_path.exists():
        text = txt_path.read_text(encoding="utf-8")
    else:
        text = gsis.pdf_text(pdf_path.read_bytes())
        txt_path.write_text(text, encoding="utf-8")
    blocks = [block for block in DATE_RE.split(text) if "FG" in block]
    return AnnualSummary(season=season, url=url, text=text, blocks=blocks)


def norm(value: str) -> str:
    return gsis.normalize_token(value)


def game_teams(game_id: str) -> tuple[str, str]:
    _, _, away, home = game_id.split("_", 3)
    return away, home


def date_label(row: dict[str, str]) -> str:
    played = dt.date.fromisoformat(row["date"])
    return f"{played.strftime('%B')} {played.day}".upper()


def block_matches_game(block: str, rows: list[dict[str, str]]) -> bool:
    away, home = game_teams(rows[0]["game_id"])
    upper = block.upper()
    if date_label(rows[0]) not in upper:
        return False
    hits = 0
    for team in (away, home):
        if any(alias.upper() in upper for alias in TEAM_NAME_ALIASES.get(team, [team])):
            hits += 1
    return hits == 2


def team_for_prefix(prefix: str, game_id: str) -> str | None:
    away, home = game_teams(game_id)
    clean = norm(prefix)
    matches = []
    candidate_teams = tuple(TEAM_PREFIX_ALIASES) if away == home else (away, home)
    for team in candidate_teams:
        aliases = TEAM_PREFIX_ALIASES.get(team, [])
        if any(norm(alias) == clean for alias in aliases):
            matches.append(team)
    if len(matches) == 1:
        return matches[0]
    if away == home and any(norm(alias) == clean for alias in TEAM_PREFIX_ALIASES.get(away, [])):
        return away
    return None


def source_last_name(name: str) -> str:
    parts = [part for part in re.split(r"\s+", name.strip()) if part]
    return norm(parts[-1]) if parts else ""


def kicker_matches(source_name: str, player_name: str) -> bool:
    source = norm(source_name)
    expected = gsis.last_name(player_name)
    if source == expected:
        return True
    if len(source) >= 4 and expected.endswith(source):
        return True
    if not source or not expected or source[0] != expected[0]:
        return False
    return gsis.difflib.SequenceMatcher(None, source, expected).ratio() >= 0.75


def extract_fg_events(block: str, game_id: str) -> list[tuple[str, str, int]]:
    events: list[tuple[str, str, int]] = []
    for pattern in (FG_RE, REVERSE_FG_RE):
        for match in pattern.finditer(block):
            team = team_for_prefix(match.group(1), game_id)
            if not team:
                continue
            events.append((team, source_last_name(match.group(2)), int(match.group(3))))
    for match in OCR_COMPACT_FG_RE.finditer(block):
        team = team_for_prefix(match.group(1), game_id)
        if not team:
            continue
        events.append((team, source_last_name(match.group(2)), int(match.group(3))))
    return events


def distances_for_row(summary: AnnualSummary, row: dict[str, str], rows: list[dict[str, str]]) -> tuple[list[int], str]:
    away, home = game_teams(row["game_id"])
    team_matches = (lambda team: True) if away == home else (lambda team: team == row["team"])
    matching_blocks = [block for block in summary.blocks if block_matches_game(block, rows)]
    if not matching_blocks:
        return [], "no matching NFL annual scoring-summary game block found"
    if len(matching_blocks) > 1:
        lname = gsis.last_name(row["player_name"])
        fg_made = int(row["fg_made"])
        long_made = int(row["long_made_fg"])
        viable: list[list[int]] = []
        for block in matching_blocks:
            events = extract_fg_events(block, row["game_id"])
            distances = [yards for team, kicker, yards in events if team_matches(team) and kicker_matches(kicker, row["player_name"])]
            if len(distances) == fg_made and long_made in distances:
                viable.append(distances)
        if len(viable) == 1:
            return viable[0], ""
        return [], f"ambiguous NFL annual scoring-summary game block count {len(matching_blocks)}"

    events = extract_fg_events(matching_blocks[0], row["game_id"])
    lname = gsis.last_name(row["player_name"])
    distances = [yards for team, kicker, yards in events if team_matches(team) and kicker_matches(kicker, row["player_name"])]
    fg_made = int(row["fg_made"])
    long_made = int(row["long_made_fg"])
    if len(distances) != fg_made:
        same_team = [(kicker, yards) for team, kicker, yards in events if team_matches(team)]
        return distances, f"NFL annual scoring-summary distance parse mismatch: got {distances}, expected count {fg_made}; same-team events {same_team}"
    if long_made not in distances:
        return distances, f"NFL annual scoring-summary long-FG mismatch: got {distances}, expected long {long_made}"
    return distances, ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=1970)
    parser.add_argument("--end-season", type=int, default=1997)
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

    summaries: dict[int, AnnualSummary | None] = {}
    game_items = sorted(by_game.items())
    if args.limit_games:
        selected_items = game_items[: args.limit_games]
        skipped_rows = [row for _, rows in game_items[args.limit_games :] for row in rows]
        current_unresolved.extend(skipped_rows)
    else:
        selected_items = game_items

    for game_id, rows in selected_items:
        season = int(rows[0]["season"])
        if season not in summaries:
            summaries[season] = source_text(season)
        summary = summaries[season]
        if not summary:
            current_unresolved.extend({**row, "unresolved_reason": "no NFL annual scoring-summary PDF found"} for row in rows)
            gsis.print_progress(game_id, resolved, current_unresolved)
            gsis.flush_outputs(upload_rows, resolved, current_unresolved)
            continue

        for row in rows:
            distances, reason = distances_for_row(summary, row, rows)
            if not reason:
                out = {col: row[col] for col in gsis.CSV_COLUMNS if col != "fg_made_distances"}
                out["fg_made_distances"] = ",".join(str(distance) for distance in distances)
                out["gsis_url"] = summary.url
                resolved.append(out)
            else:
                current_unresolved.append({**row, "gsis_url": summary.url, "unresolved_reason": reason})
        gsis.print_progress(game_id, resolved, current_unresolved)
        gsis.flush_outputs(upload_rows, resolved, current_unresolved)

    gsis.flush_outputs(upload_rows, resolved, current_unresolved)
    print(f"resolved multi-FG rows: {len(resolved)}")
    print(f"unresolved multi-FG rows: {len(current_unresolved)}")


if __name__ == "__main__":
    main()
