"""Complete 1970-1998 kicker rows with official NFLGSIS gamebook distances.

Source policy:
- Counts come from official NFL.com kicker game logs.
- Missing multi-FG made distances come from official NFLGSIS/NFL gamebooks.

This script currently supports:
- Born-digital PDFs via PyMuPDF text extraction.
- Scanned PDFs via RapidOCR fallback for the first game-summary page.
"""

from __future__ import annotations

import csv
import argparse
import re
import concurrent.futures
import os
import difflib
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz
import requests
from rapidocr_onnxruntime import RapidOCR


BASE_DIR = Path("sample_data")
UPLOAD_IN = BASE_DIR / "nfl_official_1970_1998_upload.csv"
NEEDS_IN = BASE_DIR / "nfl_official_1970_1998_needs_gamebook_distances.csv"
FINAL_OUT = BASE_DIR / "nfl_official_1970_1998_gsis_enhanced_partial.csv"
RESOLVED_OUT = BASE_DIR / "nfl_gsis_resolved_multi_fg_rows.csv"
UNRESOLVED_OUT = BASE_DIR / "nfl_gsis_unresolved_multi_fg_rows.csv"
CACHE_DIR = BASE_DIR / ".gsis_gamebooks"
WEEK_CACHE_FILE = CACHE_DIR / "week_ids.json"

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

TEAM_ALIASES = {
    "49ERS": "SF",
    "BEARS": "CHI",
    "BENGALS": "CIN",
    "BILLS": "BUF",
    "BRONCOS": "DEN",
    "BROWNS": "CLE",
    "BUCCANEERS": "TB",
    "CARDINALS": "ARI",
    "CHARGERS": "SD",
    "CHIEFS": "KC",
    "COLTS": "IND",
    "COWBOYS": "DAL",
    "DOLPHINS": "MIA",
    "EAGLES": "PHI",
    "FALCONS": "ATL",
    "GIANTS": "NYG",
    "JAGUARS": "JAX",
    "JETS": "NYJ",
    "LIONS": "DET",
    "OILERS": "HOU",
    "PACKERS": "GB",
    "PANTHERS": "CAR",
    "PATRIOTS": "NE",
    "RAIDERS": "OAK",
    "RAMS": "LA",
    "RAVENS": "BAL",
    "REDSKINS": "WAS",
    "SAINTS": "NO",
    "SEAHAWKS": "SEA",
    "STEELERS": "PIT",
    "TITANS": "TEN",
    "VIKINGS": "MIN",
}

ABBR_TEXT_ALIASES = {
    "ARI": ["CARDINALS"],
    "BAL": ["RAVENS", "COLTS"],
    "HOU": ["OILERS"],
    "IND": ["COLTS"],
    "LA": ["RAMS", "RAIDERS"],
    "LAC": ["CHARGERS"],
    "OAK": ["RAIDERS"],
    "PHX": ["CARDINALS"],
    "SD": ["CHARGERS"],
    "STL": ["RAMS", "CARDINALS"],
    "TEN": ["OILERS", "TITANS"],
}

WEEK_ID_CACHE: dict[tuple[int, int], list[int]] = {}
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Kickergami official-source GSIS backfill"})


def cache_key(season: int, week: int) -> str:
    return f"{season}-{week:02d}"


def load_week_cache() -> None:
    if not WEEK_CACHE_FILE.exists():
        return
    data = json.loads(WEEK_CACHE_FILE.read_text(encoding="utf-8"))
    for key, ids in data.items():
        season, week = key.split("-")
        WEEK_ID_CACHE[(int(season), int(week))] = [int(value) for value in ids]


def save_week_cache() -> None:
    WEEK_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {cache_key(season, week): ids for (season, week), ids in sorted(WEEK_ID_CACHE.items())}
    WEEK_CACHE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


@dataclass(frozen=True)
class Candidate:
    season: int
    week: int
    gsis_id: int
    url: str
    text: str


def normalize_token(value: str) -> str:
    token = re.sub(r"[^A-Z0-9]", "", value.upper())
    return token.translate(str.maketrans({"0": "O", "1": "I"}))


def last_name(player_name: str) -> str:
    return normalize_token(player_name.split()[-1])


def gamebook_urls(season: int, week: int, gsis_id: int) -> list[str]:
    # Older NFLGSIS gamebooks use a case-sensitive `Reg` path; newer ones
    # commonly work with lowercase `reg`.
    variants = ["Reg", "reg"] if season < 1997 else ["reg", "Reg"]
    return [f"https://nflgsis.com/{season}/{variant}/{week:02d}/{gsis_id}/Gamebook.pdf" for variant in variants]


def gamebook_url(season: int, week: int, gsis_id: int) -> str:
    return gamebook_urls(season, week, gsis_id)[0]


def pdf_text(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def ocr_first_page(content: bytes, ocr: RapidOCR) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    png = pix.tobytes("png")
    result, _ = ocr(png)
    if not result:
        return ""
    return "\n".join(item[1] for item in result)


def ocr_first_page_cached(cache_path: Path, content: bytes, ocr: RapidOCR) -> str:
    text_path = cache_path.with_suffix(".ocr.txt")
    if text_path.exists():
        return text_path.read_text(encoding="utf-8")
    text = ocr_first_page(content, ocr)
    text_path.write_text(text, encoding="utf-8")
    return text


def fetch_candidate(season: int, week: int, gsis_id: int, ocr: RapidOCR | None = None) -> Candidate | None:
    cache_path = CACHE_DIR / str(season) / f"{week:02d}" / f"{gsis_id}.pdf"
    url = gamebook_url(season, week, gsis_id)
    if cache_path.exists():
        content = cache_path.read_bytes()
    else:
        content = b""
        for candidate_url in gamebook_urls(season, week, gsis_id):
            response = SESSION.get(candidate_url, timeout=30)
            if response.status_code == 200 and response.content.startswith(b"%PDF"):
                url = candidate_url
                content = response.content
                break
        if not content:
            return None
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)
    if not content.startswith(b"%PDF"):
        return None

    text = pdf_text(content)
    if ocr and season <= 1996:
        ocr_text = ocr_first_page_cached(cache_path, content, ocr)
        text = f"{text}\n{ocr_text}" if text.strip() else ocr_text
    elif len(text.strip()) < 500 and ocr:
        text = ocr_first_page_cached(cache_path, content, ocr)
    if len(text.strip()) < 100:
        return None
    return Candidate(season=season, week=week, gsis_id=gsis_id, url=url, text=text)


def text_matches_game(text: str, rows: list[dict[str, str]]) -> bool:
    upper = text.upper()
    teams = {r["team"] for r in rows} | {r["opponent"] for r in rows}
    team_hits = 0
    for team in teams:
        aliases = ABBR_TEXT_ALIASES.get(team, [])
        aliases.extend(alias for alias, abbr in TEAM_ALIASES.items() if abbr == team)
        if any(alias in upper for alias in aliases):
            team_hits += 1
    return team_hits >= 2


def extract_from_scoring_plays(text: str) -> dict[str, list[int]]:
    found: dict[str, list[int]] = defaultdict(list)
    name_part = r"[A-Z0-9]{1,2}\.\s*[A-Za-z0-9'\-]+(?:\s+[A-Za-z0-9'\-]+)?"
    fg_words = r"F[i1le0-9]+d\s+Go\S+"
    yard_words = r"y(?:d|ard|u)\.?"
    pattern = re.compile(rf"\b({name_part})\s+(\d{{1,2}})\s+{yard_words}\s*{fg_words}", re.I)
    for name, yards in pattern.findall(text):
        found[last_name(name.replace(".", " "))].append(int(yards))
    legacy_pattern = re.compile(r"\bFG\s+([A-Z][A-Z'\-]+)\s*(\d{2})\b", re.I)
    for name, yards in legacy_pattern.findall(text):
        found[normalize_token(name)].append(int(yards))
    reverse_legacy = re.compile(r"\b([A-Z][A-Za-z'\-]+)\s+(\d{2})\s+FG\b", re.I)
    for name, yards in reverse_legacy.findall(text):
        found[normalize_token(name)].append(int(yards))
    ocr_fg = re.compile(r"\b[FE]G[_\s]+([A-Z][A-Z'\-]+)[._\s]*(\d{2})\s*(?:yds?)?\b", re.I)
    for name, yards in ocr_fg.findall(text):
        found[normalize_token(name)].append(int(yards))
    made_summary = re.compile(r"(?=\bMADE\s*:\s*[^A-Z0-9]{0,5}([A-Z][A-Z'\-]+)(.{0,90}))", re.I | re.S)
    for name, tail in made_summary.findall(text):
        tail = re.split(r"\b(?:FIELD|MISSED|SCORING|ATTEMPT|TOTALS?|HOME|VISITORS?)\b", tail, maxsplit=1, flags=re.I)[0]
        distances = [int(value) for value in re.findall(r"\b\d{2}\b", tail)]
        if distances:
            found[normalize_token(name)].extend(distances)
    return found


def extract_from_summary_blob(text: str, rows: list[dict[str, str]]) -> dict[str, list[int]]:
    compact = re.sub(r"\s+", " ", text.upper().replace("YDS", "YDS "))
    found: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        lname = last_name(row["player_name"])
        idx = normalize_token(compact).find(lname)
        if idx < 0:
            continue
        # Use the unnormalized neighborhood; OCR often interleaves but the kicker's
        # distance list generally stays close to the name.
        raw_idx = compact.find(row["player_name"].split()[-1].upper())
        if raw_idx < 0:
            raw_idx = max(0, idx)
        chunk = compact[raw_idx : raw_idx + 240]
        distances: list[int] = []
        for match in re.finditer(r"(\d{1,2})\s*YDS?(?:[- ]*NO\s*G(?:OO)?D)?", chunk, re.I):
            token = match.group(0).upper()
            if "NO" in token:
                continue
            distances.append(int(match.group(1)))
        if distances:
            found[lname].extend(distances)
        legacy = re.search(rf"{re.escape(lname)}\s*[-:]\s*((?:\d{{2}}\s*,?\s*)+)", compact, re.I)
        if legacy:
            found[lname].extend(int(value) for value in re.findall(r"\d{2}", legacy.group(1)))
    return found


def distances_for_rows(candidate: Candidate, rows: list[dict[str, str]]) -> dict[str, list[int]]:
    merged = extract_from_scoring_plays(candidate.text)
    summary = extract_from_summary_blob(candidate.text, rows)
    for key, values in summary.items():
        if len(values) > len(merged.get(key, [])):
            merged[key] = values
    return merged


def clean_distances(distances: list[int], count: int) -> list[int]:
    if len(distances) >= count * 2 and distances[:count] == distances[count : count * 2]:
        return distances[:count]
    unique: list[int] = []
    for distance in distances:
        if distance not in unique:
            unique.append(distance)
    if len(unique) >= count:
        return unique[:count]
    return distances[:count]


def distances_for_player(distances_by_name: dict[str, list[int]], player_name: str) -> list[int]:
    lname = last_name(player_name)
    if lname in distances_by_name:
        return distances_by_name[lname]
    candidates = [
        key
        for key in distances_by_name
        if key and key[0] == lname[0] and difflib.SequenceMatcher(None, key, lname).ratio() >= 0.72
    ]
    if len(candidates) == 1:
        return distances_by_name[candidates[0]]
    return []


def candidate_ranges(season: int) -> Iterable[range]:
    if season >= 1997:
        yield range(1, 700)
    elif season >= 1981:
        approx = 13600 + (season - 1981) * 260
        yield range(max(1, approx - 350), approx + 500)
    else:
        yield range(1, 1)


def discover_week_ids(season: int, week: int) -> list[int]:
    key = (season, week)
    if key in WEEK_ID_CACHE and WEEK_ID_CACHE[key]:
        return WEEK_ID_CACHE[key]

    local_dir = CACHE_DIR / str(season) / f"{week:02d}"
    if local_dir.exists():
        local_ids = sorted(int(path.stem) for path in local_dir.glob("*.pdf") if path.stem.isdigit())
        if local_ids:
            WEEK_ID_CACHE[key] = local_ids
            save_week_cache()
            return local_ids

    ids: list[int] = []
    def check(gsis_id: int) -> int | None:
        try:
            for url in gamebook_urls(season, week, gsis_id):
                response = SESSION.head(url, timeout=8, allow_redirects=True)
                if response.status_code == 200 and "pdf" in response.headers.get("content-type", "").lower():
                    return gsis_id
        except requests.RequestException:
            return None
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        for found in executor.map(check, [i for r in candidate_ranges(season) for i in r]):
            if found is not None:
                ids.append(found)

    WEEK_ID_CACHE[key] = sorted(ids)
    save_week_cache()
    return WEEK_ID_CACHE[key]


def find_gamebook(rows: list[dict[str, str]], ocr: RapidOCR) -> Candidate | None:
    season = int(rows[0]["season"])
    week = int(rows[0]["week"])
    candidates: list[Candidate] = []
    for gsis_id in discover_week_ids(season, week):
        candidate = fetch_candidate(season, week, gsis_id)
        if not candidate:
            continue
        candidates.append(candidate)
        if text_matches_game(candidate.text, rows):
            if season < 1997:
                return fetch_candidate(season, week, gsis_id, ocr)
            return candidate
    if season < 1997:
        for candidate in candidates:
            ocr_candidate = fetch_candidate(season, week, candidate.gsis_id, ocr)
            if ocr_candidate and text_matches_game(ocr_candidate.text, rows):
                return ocr_candidate
    return None


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    for attempt in range(5):
        try:
            os.replace(tmp_path, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(1 + attempt)


def flush_outputs(upload_rows: list[dict[str, str]], resolved: list[dict[str, str]], unresolved: list[dict[str, str]]) -> None:
    merged = {(row["game_id"], row["player_id"]): {col: row[col] for col in CSV_COLUMNS} for row in upload_rows}
    for row in resolved:
        merged[(row["game_id"], row["player_id"])] = {col: row[col] for col in CSV_COLUMNS}
    write_rows(FINAL_OUT, sorted(merged.values(), key=lambda r: (r["date"], r["game_id"], r["player_name"])), CSV_COLUMNS)
    write_rows(RESOLVED_OUT, resolved, CSV_COLUMNS + ["gsis_url"])
    write_rows(UNRESOLVED_OUT, unresolved, list(unresolved[0].keys()) if unresolved else CSV_COLUMNS + ["gsis_url", "unresolved_reason"])


def print_progress(game_id: str, resolved: list[dict[str, str]], unresolved: list[dict[str, str]]) -> None:
    try:
        print(game_id, "resolved", len(resolved), "unresolved", len(unresolved), flush=True)
    except OSError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=1970)
    parser.add_argument("--end-season", type=int, default=1998)
    parser.add_argument("--limit-games", type=int, default=0)
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--retry-unresolved", action="store_true")
    args = parser.parse_args()
    load_week_cache()

    upload_rows = read_rows(UPLOAD_IN)
    existing_resolved = read_rows(RESOLVED_OUT) if args.append else []
    existing_unresolved = read_rows(UNRESOLVED_OUT) if args.append else []
    outside_unresolved = [
        row
        for row in existing_unresolved
        if not (args.start_season <= int(row["season"]) <= args.end_season)
    ]
    resolved_keys = {(row["game_id"], row["player_id"]) for row in existing_resolved}
    unresolved_keys = set() if args.retry_unresolved else {(row["game_id"], row["player_id"]) for row in existing_unresolved}
    needs_rows = [
        row
        for row in read_rows(NEEDS_IN)
        if args.start_season <= int(row["season"]) <= args.end_season
        and (row["game_id"], row["player_id"]) not in resolved_keys
        and (row["game_id"], row["player_id"]) not in unresolved_keys
    ]
    by_game: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in needs_rows:
        by_game[row["game_id"]].append(row)

    ocr = RapidOCR()
    resolved: list[dict[str, str]] = list(existing_resolved)
    unresolved: list[dict[str, str]] = list(outside_unresolved if args.retry_unresolved else existing_unresolved)
    for idx, (game_id, rows) in enumerate(sorted(by_game.items()), start=1):
        if args.limit_games and idx > args.limit_games:
            break
        candidate = find_gamebook(rows, ocr)
        if not candidate:
            unresolved.extend({**row, "gsis_url": "", "unresolved_reason": "no matching GSIS gamebook found"} for row in rows)
            print_progress(game_id, resolved, unresolved)
            flush_outputs(upload_rows, resolved, unresolved)
            continue
        distances_by_name = distances_for_rows(candidate, rows)
        for row in rows:
            distances = distances_for_player(distances_by_name, row["player_name"])
            fg_made = int(row["fg_made"])
            distances = clean_distances(distances, fg_made)
            if len(distances) == fg_made:
                out = {col: row[col] for col in CSV_COLUMNS if col != "fg_made_distances"}
                out["fg_made_distances"] = ",".join(str(d) for d in distances)
                out["gsis_url"] = candidate.url
                resolved.append(out)
            else:
                unresolved.append(
                    {
                        **row,
                        "gsis_url": candidate.url,
                        "unresolved_reason": f"distance parse mismatch: got {distances}, expected count {fg_made}",
                    }
                )
        print_progress(game_id, resolved, unresolved)
        flush_outputs(upload_rows, resolved, unresolved)

    flush_outputs(upload_rows, resolved, unresolved)
    print(f"final rows: {len(upload_rows) + len(resolved)}")
    print(f"resolved multi-FG rows: {len(resolved)}")
    print(f"unresolved multi-FG rows: {len(unresolved)}")


if __name__ == "__main__":
    main()
