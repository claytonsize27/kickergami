"""Apply conservative official club media-guide distance resolutions."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
import complete_nfl_gsis_distances as gsis


BASE_DIR = Path("sample_data")
UPLOAD_IN = BASE_DIR / "nfl_official_1970_1998_upload.csv"
FINAL_OUT = BASE_DIR / "nfl_official_1970_1998_gsis_enhanced_partial.csv"
RESOLVED_OUT = BASE_DIR / "nfl_gsis_resolved_multi_fg_rows.csv"
UNRESOLVED_OUT = BASE_DIR / "nfl_gsis_unresolved_multi_fg_rows.csv"

SAINTS_1971_GUIDE = "https://static.clubs.nfl.com/image/upload/saints/tecwancwttvcxqnxkoqm.pdf"
SAINTS_RECORD_FACT_BOOK = "https://static.clubs.nfl.com/image/upload/saints/zupknbzryc6xiedwrojn.pdf"
NFL_1997_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151436/1997.pdf"
NFL_1996_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151433/1996.pdf"
NFL_1984_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150546/1984.pdf"
NFL_1983_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150505/1983.pdf"
NFL_1990_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150948/1990.pdf"
NFL_1981_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150347/1981.pdf"
NFL_1988_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150831/1988.pdf"
NFL_1989_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150907/1989.pdf"
NFL_1994_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151222/1994.pdf"
NFL_1995_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151420/1995.pdf"
NFL_1993_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151144/1993.pdf"
NFL_1992_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151103/1992.pdf"
NFL_1986_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150709/1986.pdf"
NFL_1982_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150423/1982.pdf"
NFL_1979_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150229/1979.pdf"
NFL_1977_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150108/1977.pdf"
NFL_1975_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145853/1975.pdf"
NFL_1991_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151026/1991.pdf"
NFL_1987_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150746/1987.pdf"
NFL_1985_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150628/1985.pdf"
NFL_1980_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150309/1980.pdf"
NFL_1978_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150149/1978.pdf"
NFL_1976_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150027/1976.pdf"
NFL_1972_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145652/1972.pdf"
NFL_1971_ANNUAL_SUMMARY = "https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145600/1971.pdf"

# Verified from the 1971 New Orleans Saints media guide, "How It Happened
# in 1970" scoring summaries. These are explicit scoring-play lines such as
# "Los Angeles-Field Goal, Ray43" and "New Orleans-FieldGoal,Dempsey54".
VERIFIED_DISTANCES = {
    ("1970_07_LA_NO", "nfl-david-ray"): ([43, 14, 23], SAINTS_1971_GUIDE),
    ("1970_12_NO_LA", "nfl-david-ray"): ([45, 37], SAINTS_1971_GUIDE),
    ("1970_12_NO_LA", "nfl-tom-dempsey"): ([24, 50, 54], SAINTS_1971_GUIDE),
    ("1995_10_STL_SF", "nfl-doug-brien"): ([35, 26, 47, 42], SAINTS_RECORD_FACT_BOOK),
}

# Verified from Pro Football Reference scoring summaries, with a second source
# where the distance list intentionally overrides NFL.com's incorrect `Lng`.
VERIFIED_EXTERNAL_ROWS = {
    ("1990_14_PHX_ATL", "nfl-greg-davis"): (
        [41, 24],
        "https://www.pro-football-reference.com/boxscores/199012090atl.htm; corroborated_by=" + NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1991_05_DEN_MIN", "nfl-david-treadwell"): (
        [37, 32],
        "https://www.pro-football-reference.com/boxscores/199109290min.htm; corroborated_by=" + NFL_1991_ANNUAL_SUMMARY,
    ),
    ("1991_07_NO_PHI", "nfl-roger-ruzek"): (
        [38, 41],
        "https://www.pro-football-reference.com/boxscores/199110130phi.htm; corroborated_by=" + NFL_1991_ANNUAL_SUMMARY,
    ),
    ("1991_09_GB_TB", "nfl-chris-jacke"): (
        [34, 46],
        "https://www.pro-football-reference.com/boxscores/199110270tam.htm; corroborated_by=" + NFL_1991_ANNUAL_SUMMARY,
    ),
    ("1993_04_SF_NO", "nfl-morten-andersen"): (
        [33, 39, 39],
        "https://www.pro-football-reference.com/boxscores/199309260nor.htm; corroborated_by=" + NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1993_10_BUF_NE", "nfl-steve-christie"): (
        [27, 30],
        "https://www.pro-football-reference.com/boxscores/199311070nwe.htm; corroborated_by=" + NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1993_11_ATL_LA", "nfl-norm-johnson"): (
        [46, 44],
        "https://www.pro-football-reference.com/boxscores/199311140ram.htm; corroborated_by=" + NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1993_14_CIN_SF", "nfl-doug-pelfrey"): (
        [38, 29],
        "https://www.pro-football-reference.com/boxscores/199312050sfo.htm; corroborated_by=" + NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1994_02_CIN_SD", "nfl-john-carney"): (
        [38, 20],
        "https://www.pro-football-reference.com/boxscores/199409110sdg.htm; corroborated_by=" + NFL_1994_ANNUAL_SUMMARY,
    ),
    ("1994_14_NYG_CLE", "nfl-brad-daluiso"): (
        [25, 30, 33],
        "https://www.pro-football-reference.com/boxscores/199412040cle.htm; corroborated_by=https://www.latimes.com/archives/la-xpm-1994-12-05-sp-5103-story.html",
    ),
    ("1994_17_PHI_CIN", "nfl-eddie-murray"): (
        [34, 23, 35],
        "https://www.pro-football-reference.com/boxscores/199412240cin.htm; corroborated_by=" + NFL_1994_ANNUAL_SUMMARY,
    ),
    ("1996_13_ATL_CIN", "nfl-doug-pelfrey"): (
        [37, 20],
        "https://www.pro-football-reference.com/boxscores/199611240cin.htm; corroborated_by=" + NFL_1996_ANNUAL_SUMMARY,
    ),
    ("1971_02_DET_NE", "nfl-errol-mann"): (
        [23, 27],
        "https://www.pro-football-reference.com/boxscores/197109260nwe.htm; corroborated_by=" + NFL_1971_ANNUAL_SUMMARY,
    ),
    ("1971_05_PIT_KC", "nfl-roy-gerela"): (
        [32, 40, 35],
        "https://www.pro-football-reference.com/boxscores/197110180kan.htm",
    ),
    ("1971_14_DEN_OAK", "nfl-jim-turner-2"): (
        [14, 29],
        "https://www.pro-football-reference.com/boxscores/197112190rai.htm; corroborated_by=" + NFL_1971_ANNUAL_SUMMARY,
    ),
    ("1975_04_DEN_PIT", "nfl-jim-turner-2"): (
        [22, 39, 36],
        "https://www.pro-football-reference.com/boxscores/197510120pit.htm; corroborated_by=" + NFL_1975_ANNUAL_SUMMARY,
    ),
    ("1977_10_ATL_NO", "nfl-fred-steinfort"): (
        [36, 40],
        "https://www.pro-football-reference.com/boxscores/197711200nor.htm; corroborated_by=" + NFL_1977_ANNUAL_SUMMARY,
    ),
    ("1977_14_CLE_SEA", "nfl-don-cockroft"): (
        [24, 33],
        "https://www.pro-football-reference.com/boxscores/197712180sea.htm; corroborated_by=" + NFL_1977_ANNUAL_SUMMARY,
    ),
    ("1979_14_NE_MIA", "nfl-uwe-von-schamann"): (
        [31, 33, 27],
        "https://www.pro-football-reference.com/boxscores/197911290mia.htm; corroborated_by=" + NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1974_11_NE_BAL", "nfl-john-smith-2"): (
        [33, 28],
        "https://ultimate70s.com/nflbox/19741124/ALL/N; corroborated_by=https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28145810/1974.pdf",
    ),
    ("1979_16_GB_DET", "nfl-tom-birney"): (
        [27, 25, 47, 41],
        "https://www.pro-football-reference.com/boxscores/197912150det.htm; corroborated_by=" + NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1979_16_SEA_OAK", "nfl-efren-herrera"): (
        [24, 43],
        "https://www.pro-football-reference.com/boxscores/197912160rai.htm; corroborated_by=" + NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1980_02_LA_TB", "nfl-frank-corral"): (
        [43, 32, 27],
        "https://www.pro-football-reference.com/boxscores/198009110tam.htm; corroborated_by=" + NFL_1980_ANNUAL_SUMMARY,
    ),
    ("1982_01_SD_DEN", "nfl-rolf-benirschke"): (
        [50, 24, 40],
        "https://www.pro-football-reference.com/boxscores/198209120den.htm; corroborated_by=" + NFL_1982_ANNUAL_SUMMARY,
    ),
    ("1985_11_MIA_IND", "nfl-raul-allegre"): (
        [28, 32],
        "https://www.pro-football-reference.com/boxscores/198511170clt.htm; corroborated_by=" + NFL_1985_ANNUAL_SUMMARY,
    ),
    ("1985_12_WAS_PIT", "nfl-gary-anderson"): (
        [22, 37, 27],
        "https://www.pro-football-reference.com/boxscores/198511240pit.htm",
    ),
    ("1985_15_CHI_NYJ", "nfl-kevin-butler"): (
        [18, 31, 37, 21],
        "https://www.pro-football-reference.com/boxscores/198512140nyj.htm; corroborated_by=" + NFL_1985_ANNUAL_SUMMARY,
    ),
    ("1986_02_CLE_HOU", "nfl-tony-zendejas"): (
        [35, 36],
        "https://www.pro-football-reference.com/boxscores/198609140oti.htm; corroborated_by=" + NFL_1986_ANNUAL_SUMMARY,
    ),
    ("1986_08_TB_KC", "nfl-donald-igwebuike"): (
        [49, 39],
        "https://www.pro-football-reference.com/boxscores/198610260kan.htm; corroborated_by=" + NFL_1986_ANNUAL_SUMMARY,
    ),
    ("1986_15_SF_NE", "nfl-ray-wersching"): (
        [46, 31, 20],
        "https://www.pro-football-reference.com/boxscores/198612140nwe.htm; corroborated_by=" + NFL_1986_ANNUAL_SUMMARY,
    ),
    ("1987_07_IND_NYJ", "nfl-dean-biasucci"): (
        [36, 44, 38, 33],
        "https://www.pro-football-reference.com/boxscores/198711010nyj.htm; corroborated_by=" + NFL_1987_ANNUAL_SUMMARY,
    ),
    ("1987_08_MIA_CIN", "nfl-fuad-reveiz"): (
        [47, 34],
        "https://www.pro-football-reference.com/boxscores/198711080cin.htm; corroborated_by=" + NFL_1987_ANNUAL_SUMMARY,
    ),
    ("1988_10_NO_WAS", "nfl-chip-lohmiller"): (
        [32, 23],
        "https://www.pro-football-reference.com/boxscores/198811060was.htm; corroborated_by=" + NFL_1988_ANNUAL_SUMMARY,
    ),
    ("1990_03_DET_TB", "nfl-steve-christie"): (
        [55, 28, 21],
        "https://www.pro-football-reference.com/boxscores/199009230tam.htm; corroborated_by=" + NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1990_14_PHI_MIA", "nfl-pete-stoyanovich"): (
        [24, 34, 34],
        "https://www.pro-football-reference.com/boxscores/199012090mia.htm; corroborated_by=" + NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1991_04_CLE_NYG", "nfl-matt-bahr"): (
        [44, 48],
        "https://www.pro-football-reference.com/boxscores/199109220nyg.htm; corroborated_by=" + NFL_1991_ANNUAL_SUMMARY,
    ),
    ("1994_13_NE_IND", "nfl-matt-bahr"): (
        [22, 37, 25, 43],
        "https://www.pro-football-reference.com/boxscores/199411270clt.htm; corroborated_by=" + NFL_1994_ANNUAL_SUMMARY,
    ),
    ("1972_08_STL_PHI", "nfl-tom-dempsey"): (
        [11, 30],
        NFL_1972_ANNUAL_SUMMARY,
    ),
    ("1975_12_WAS_ATL", "nfl-nick-mike-mayer"): (
        [23, 44],
        NFL_1975_ANNUAL_SUMMARY,
    ),
    ("1977_02_ATL_WAS", "nfl-nick-mike-mayer"): (
        [23, 27],
        NFL_1977_ANNUAL_SUMMARY,
    ),
    ("1977_12_OAK_LA", "nfl-rafael-septien"): (
        [21, 44],
        NFL_1977_ANNUAL_SUMMARY,
    ),
    ("1979_10_BAL_GB", "nfl-toni-linhart"): (
        [24, 39],
        NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1982_09_ATL_NO", "nfl-mick-luckhurst"): (
        [40, 29],
        NFL_1982_ANNUAL_SUMMARY,
    ),
    ("1971_03_WAS_DAL", "nfl-curt-knight"): (
        [25, 32],
        "https://www.pro-football-reference.com/boxscores/197110030dal.htm",
    ),
    ("1976_05_BUF_GB", "nfl-john-leypoldt"): (
        [48, 44],
        "https://www.pro-football-reference.com/boxscores/197610100gnb.htm",
    ),
    ("1976_05_PIT_CLE", "nfl-don-cockroft"): (
        [43, 28, 50, 40],
        "https://www.pro-football-reference.com/boxscores/197610100cle.htm; corroborated_by=https://www.brownsnation.com/don-cockroft/",
    ),
    ("1976_06_BUF_TB", "nfl-john-leypoldt"): (
        [25, 39],
        "https://www.pro-football-reference.com/boxscores/197610170tam.htm",
    ),
    ("1980_01_DEN_PHI", "nfl-tony-franklin-2"): (
        [17, 35],
        "https://www.pro-football-reference.com/boxscores/198009070phi.htm; corroborated_by=https://justapedia.org/wiki/1980_Philadelphia_Eagles_season",
    ),
    ("1994_14_ATL_SF", "nfl-doug-brien"): (
        [24, 36, 32],
        "https://www.pro-football-reference.com/boxscores/199412040sfo.htm; corroborated_by=https://www.jt-sw.com/football/boxes/index.nsf/Games/1994-14-atl-sf",
    ),
    ("1978_11_TB_DET", "nfl-neil-o-donoghue"): (
        [27, 49, 28],
        "https://www.buccaneersfan.com/Pages/TeamZone/Gameday/Lions/1978-11-12.htm; corroborated_by=" + NFL_1978_ANNUAL_SUMMARY,
    ),
    ("1980_02_NO_CHI", "nfl-bob-thomas"): (
        [37, 35],
        "https://www.pro-football-reference.com/boxscores/198009140chi.htm; corroborated_by=" + NFL_1980_ANNUAL_SUMMARY,
    ),
    ("1980_10_DET_MIN", "nfl-rick-danmeier"): (
        [27, 23],
        "https://www.pro-football-reference.com/boxscores/198011090min.htm; corroborated_by=" + NFL_1980_ANNUAL_SUMMARY,
    ),
    ("1983_13_GB_ATL", "nfl-jan-stenerud"): (
        [23, 33],
        "https://www.pro-football-reference.com/boxscores/198311270atl.htm; corroborated_by=" + NFL_1983_ANNUAL_SUMMARY,
    ),
    ("1983_15_CLE_HOU", "nfl-florian-kempf"): (
        [40, 35],
        "https://www.pro-football-reference.com/boxscores/198312110oti.htm; corroborated_by=" + NFL_1983_ANNUAL_SUMMARY,
    ),
    ("1984_02_KC_CIN", "nfl-jim-breech"): (
        [48, 29],
        "https://www.pro-football-reference.com/boxscores/198409090cin.htm; corroborated_by=" + NFL_1984_ANNUAL_SUMMARY,
    ),
    ("1984_08_CLE_CIN", "nfl-matt-bahr"): (
        [50, 47],
        "https://www.pro-football-reference.com/boxscores/198410210cin.htm; corroborated_by=" + NFL_1984_ANNUAL_SUMMARY,
    ),
    ("1984_12_NYJ_HOU", "nfl-pat-leahy"): (
        [19, 26],
        "https://www.pro-football-reference.com/boxscores/198411180oti.htm; corroborated_by=" + NFL_1984_ANNUAL_SUMMARY,
    ),
    ("1985_02_CIN_STL", "nfl-jim-breech"): (
        [33, 47],
        "https://www.pro-football-reference.com/boxscores/198509150crd.htm; corroborated_by=" + NFL_1985_ANNUAL_SUMMARY,
    ),
    ("1987_08_LA_MIN", "nfl-chris-bahr"): (
        [21, 25],
        "https://www.pro-football-reference.com/boxscores/198711080min.htm; corroborated_by=" + NFL_1987_ANNUAL_SUMMARY,
    ),
    ("1993_13_PHX_NYG", "nfl-david-treadwell"): (
        [22, 37, 22],
        "https://www.pro-football-reference.com/boxscores/199311280nyg.htm; corroborated_by=" + NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1993_18_DAL_NYG", "nfl-david-treadwell"): (
        [29, 32],
        "https://www.pro-football-reference.com/boxscores/199401020nyg.htm; corroborated_by=" + NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1995_12_HOU_KC", "nfl-lin-elliott"): (
        [47, 21],
        "https://www.pro-football-reference.com/boxscores/199511190kan.htm; corroborated_by=" + NFL_1995_ANNUAL_SUMMARY,
    ),
}

# NFL.com's 1997 Greg Davis game log uses the correct per-game counts but the
# row builder attributed his post-Minnesota games to the Vikings. These rows
# are verified from the official 1997 annual scoring summary under the corrected
# San Diego Chargers game identity. The Oct. 5 six-FG row is also corroborated
# by official Chargers/Raiders game-release record-book entries.
VERIFIED_CORRECTED_ROWS = {
    ("1982_07_GB_NE", "nfl-danny-miller"): (
        {
            "date": "1982-12-19",
            "season": "1982",
            "week": "7",
            "season_type": "REG",
            "game_id": "1982_07_GB_BAL",
            "player_id": "nfl-danny-miller",
            "player_name": "Danny Miller",
            "team": "BAL",
            "opponent": "GB",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "23,40",
        },
        NFL_1982_ANNUAL_SUMMARY,
    ),
    ("1982_08_NE_SD", "nfl-danny-miller"): (
        {
            "date": "1982-12-26",
            "season": "1982",
            "week": "8",
            "season_type": "REG",
            "game_id": "1982_08_BAL_SD",
            "player_id": "nfl-danny-miller",
            "player_name": "Danny Miller",
            "team": "BAL",
            "opponent": "SD",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "46,58",
        },
        NFL_1982_ANNUAL_SUMMARY,
    ),
    ("1987_15_GB_DAL", "nfl-al-del-greco"): (
        {
            "date": "1987-12-27",
            "season": "1987",
            "week": "15",
            "season_type": "REG",
            "game_id": "1987_15_STL_DAL",
            "player_id": "nfl-al-del-greco",
            "player_name": "Al Del Greco",
            "team": "STL",
            "opponent": "DAL",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "3",
            "fg_attempts": "3",
            "fg_made_distances": "32,28,37",
        },
        NFL_1987_ANNUAL_SUMMARY,
    ),
    ("1988_11_IND_PHI", "nfl-dale-dawson"): (
        {
            "date": "1988-11-13",
            "season": "1988",
            "week": "11",
            "season_type": "REG",
            "game_id": "1988_11_IND_GB",
            "player_id": "nfl-dale-dawson",
            "player_name": "Dale Dawson",
            "team": "GB",
            "opponent": "IND",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "22,20",
        },
        NFL_1988_ANNUAL_SUMMARY,
    ),
    ("1989_15_DAL_NO", "nfl-roger-ruzek"): (
        {
            "date": "1989-12-18",
            "season": "1989",
            "week": "15",
            "season_type": "REG",
            "game_id": "1989_15_PHI_NO",
            "player_id": "nfl-roger-ruzek",
            "player_name": "Roger Ruzek",
            "team": "PHI",
            "opponent": "NO",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "21,19",
        },
        NFL_1989_ANNUAL_SUMMARY,
    ),
    ("1989_15_WAS_NE", "nfl-greg-davis"): (
        {
            "date": "1989-12-17",
            "season": "1989",
            "week": "15",
            "season_type": "REG",
            "game_id": "1989_15_WAS_ATL",
            "player_id": "nfl-greg-davis",
            "player_name": "Greg Davis",
            "team": "ATL",
            "opponent": "WAS",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "3",
            "fg_attempts": "4",
            "fg_made_distances": "33,24,32",
        },
        NFL_1989_ANNUAL_SUMMARY,
    ),
    ("1991_16_MIA_NYJ", "nfl-charlie-baumann"): (
        {
            "date": "1991-12-15",
            "season": "1991",
            "week": "16",
            "season_type": "REG",
            "game_id": "1991_16_NE_NYJ",
            "player_id": "nfl-charlie-baumann",
            "player_name": "Charlie Baumann",
            "team": "NE",
            "opponent": "NYJ",
            "xp_made": "0",
            "xp_attempts": "0",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "45,41",
        },
        NFL_1991_ANNUAL_SUMMARY,
    ),
    ("1991_17_NYG_MIA", "nfl-raul-allegre"): (
        {
            "date": "1991-12-22",
            "season": "1991",
            "week": "17",
            "season_type": "REG",
            "game_id": "1991_17_NYJ_MIA",
            "player_id": "nfl-raul-allegre",
            "player_name": "Raul Allegre",
            "team": "NYJ",
            "opponent": "MIA",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "3",
            "fg_attempts": "4",
            "fg_made_distances": "25,44,30",
        },
        NFL_1991_ANNUAL_SUMMARY,
    ),
    ("1977_14_NYJ_ATL", "nfl-nick-mike-mayer"): (
        {
            "date": "1977-12-18",
            "season": "1977",
            "week": "14",
            "season_type": "REG",
            "game_id": "1977_14_NYJ_PHI",
            "player_id": "nfl-nick-mike-mayer",
            "player_name": "Nick Mike-Mayer",
            "team": "PHI",
            "opponent": "NYJ",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "39,41",
        },
        NFL_1977_ANNUAL_SUMMARY,
    ),
    ("1979_08_STL_LA", "nfl-mike-wood"): (
        {
            "date": "1979-10-21",
            "season": "1979",
            "week": "8",
            "season_type": "REG",
            "game_id": "1979_08_SD_LA",
            "player_id": "nfl-mike-wood",
            "player_name": "Mike Wood",
            "team": "SD",
            "opponent": "LA",
            "xp_made": "4",
            "xp_attempts": "5",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "37,31",
        },
        NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1979_10_STL_KC", "nfl-mike-wood"): (
        {
            "date": "1979-11-04",
            "season": "1979",
            "week": "10",
            "season_type": "REG",
            "game_id": "1979_10_SD_KC",
            "player_id": "nfl-mike-wood",
            "player_name": "Mike Wood",
            "team": "SD",
            "opponent": "KC",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "31,26",
        },
        NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1979_11_STL_CIN", "nfl-mike-wood"): (
        {
            "date": "1979-11-11",
            "season": "1979",
            "week": "11",
            "season_type": "REG",
            "game_id": "1979_11_SD_CIN",
            "player_id": "nfl-mike-wood",
            "player_name": "Mike Wood",
            "team": "SD",
            "opponent": "CIN",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "4",
            "fg_attempts": "4",
            "fg_made_distances": "22,42,34,32",
        },
        NFL_1979_ANNUAL_SUMMARY,
    ),
    ("1982_08_DET_LA", "nfl-bob-thomas"): (
        {
            "date": "1982-12-26",
            "season": "1982",
            "week": "8",
            "season_type": "REG",
            "game_id": "1982_08_CHI_LA",
            "player_id": "nfl-bob-thomas",
            "player_name": "Bob Thomas",
            "team": "CHI",
            "opponent": "LA",
            "xp_made": "4",
            "xp_attempts": "4",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "41,31",
        },
        NFL_1982_ANNUAL_SUMMARY,
    ),
    ("1982_09_DET_TB", "nfl-bob-thomas"): (
        {
            "date": "1983-01-02",
            "season": "1982",
            "week": "9",
            "season_type": "REG",
            "game_id": "1982_09_CHI_TB",
            "player_id": "nfl-bob-thomas",
            "player_name": "Bob Thomas",
            "team": "CHI",
            "opponent": "TB",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "3",
            "fg_attempts": "4",
            "fg_made_distances": "43,19,40",
        },
        NFL_1982_ANNUAL_SUMMARY,
    ),
    ("1986_13_HOU_WAS", "nfl-mark-moseley"): (
        {
            "date": "1986-11-30",
            "season": "1986",
            "week": "13",
            "season_type": "REG",
            "game_id": "1986_13_HOU_CLE",
            "player_id": "nfl-mark-moseley",
            "player_name": "Mark Moseley",
            "team": "CLE",
            "opponent": "HOU",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "23,29",
        },
        NFL_1986_ANNUAL_SUMMARY,
    ),
    ("1986_15_WAS_CIN", "nfl-mark-moseley"): (
        {
            "date": "1986-12-14",
            "season": "1986",
            "week": "15",
            "season_type": "REG",
            "game_id": "1986_15_CLE_CIN",
            "player_id": "nfl-mark-moseley",
            "player_name": "Mark Moseley",
            "team": "CLE",
            "opponent": "CIN",
            "xp_made": "4",
            "xp_attempts": "4",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "39,19",
        },
        NFL_1986_ANNUAL_SUMMARY,
    ),
    ("1986_16_SD_WAS", "nfl-mark-moseley"): (
        {
            "date": "1986-12-21",
            "season": "1986",
            "week": "16",
            "season_type": "REG",
            "game_id": "1986_16_SD_CLE",
            "player_id": "nfl-mark-moseley",
            "player_name": "Mark Moseley",
            "team": "CLE",
            "opponent": "SD",
            "xp_made": "5",
            "xp_attempts": "6",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "37,32",
        },
        NFL_1986_ANNUAL_SUMMARY,
    ),
    ("1992_11_CHI_KC", "nfl-eddie-murray"): (
        {
            "date": "1992-11-15",
            "season": "1992",
            "week": "11",
            "season_type": "REG",
            "game_id": "1992_11_CHI_TB",
            "player_id": "nfl-eddie-murray",
            "player_name": "Eddie Murray",
            "team": "TB",
            "opponent": "CHI",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "31,40",
        },
        NFL_1992_ANNUAL_SUMMARY,
    ),
    ("1992_14_LA_KC", "nfl-eddie-murray"): (
        {
            "date": "1992-12-06",
            "season": "1992",
            "week": "14",
            "season_type": "REG",
            "game_id": "1992_14_LA_TB",
            "player_id": "nfl-eddie-murray",
            "player_name": "Eddie Murray",
            "team": "TB",
            "opponent": "LA",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "34,47",
        },
        NFL_1992_ANNUAL_SUMMARY,
    ),
    ("1993_16_PHI_CLE", "nfl-matt-bahr"): (
        {
            "date": "1993-12-19",
            "season": "1993",
            "week": "16",
            "season_type": "REG",
            "game_id": "1993_16_NE_CLE",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "NE",
            "opponent": "CLE",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "23,34",
        },
        NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1993_18_MIA_PHI", "nfl-matt-bahr"): (
        {
            "date": "1994-01-02",
            "season": "1993",
            "week": "18",
            "season_type": "REG",
            "game_id": "1993_18_MIA_NE",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "NE",
            "opponent": "MIA",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "31,37",
        },
        NFL_1993_ANNUAL_SUMMARY,
    ),
    ("1976_07_BUF_SEA", "nfl-benny-ricardo"): (
        {
            "date": "1976-10-24",
            "season": "1976",
            "week": "7",
            "season_type": "REG",
            "game_id": "1976_07_DET_SEA",
            "player_id": "nfl-benny-ricardo",
            "player_name": "Benny Ricardo",
            "team": "DET",
            "opponent": "SEA",
            "xp_made": "5",
            "xp_attempts": "5",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "25,44",
        },
        "https://www.pro-football-reference.com/boxscores/197610240sea.htm",
    ),
    ("1976_08_GB_BUF", "nfl-benny-ricardo"): (
        {
            "date": "1976-10-31",
            "season": "1976",
            "week": "8",
            "season_type": "REG",
            "game_id": "1976_08_GB_DET",
            "player_id": "nfl-benny-ricardo",
            "player_name": "Benny Ricardo",
            "team": "DET",
            "opponent": "GB",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "34,39",
        },
        "https://ultimate70s.com/nflbox/19761031/ALL/N",
    ),
    ("1976_08_BUF_LA", "nfl-john-leypoldt"): (
        {
            "date": "1976-10-31",
            "season": "1976",
            "week": "8",
            "season_type": "REG",
            "game_id": "1976_08_SEA_LA",
            "player_id": "nfl-john-leypoldt",
            "player_name": "John Leypoldt",
            "team": "SEA",
            "opponent": "LA",
            "xp_made": "0",
            "xp_attempts": "0",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "43,41",
        },
        "https://www.pro-football-reference.com/boxscores/197610310ram.htm; corroborated_by=https://www.statmuse.com/nfl/game/10-31-1976-sea-%40-la-5788",
    ),
    ("1981_07_NO_SF", "nfl-matt-bahr"): (
        {
            "date": "1981-10-18",
            "season": "1981",
            "week": "7",
            "season_type": "REG",
            "game_id": "1981_07_NO_CLE",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "CLE",
            "opponent": "NO",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "34,19",
        },
        NFL_1981_ANNUAL_SUMMARY,
    ),
    ("1981_09_SF_BUF", "nfl-matt-bahr"): (
        {
            "date": "1981-11-01",
            "season": "1981",
            "week": "9",
            "season_type": "REG",
            "game_id": "1981_09_CLE_BUF",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "CLE",
            "opponent": "BUF",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "36,39",
        },
        NFL_1981_ANNUAL_SUMMARY,
    ),
    ("1981_10_SF_DEN", "nfl-matt-bahr"): (
        {
            "date": "1981-11-08",
            "season": "1981",
            "week": "10",
            "season_type": "REG",
            "game_id": "1981_10_CLE_DEN",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "CLE",
            "opponent": "DEN",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "27,32",
        },
        NFL_1981_ANNUAL_SUMMARY,
    ),
    ("1981_14_SF_HOU", "nfl-matt-bahr"): (
        {
            "date": "1981-12-03",
            "season": "1981",
            "week": "14",
            "season_type": "REG",
            "game_id": "1981_14_CLE_HOU",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "CLE",
            "opponent": "HOU",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "18,19",
        },
        NFL_1981_ANNUAL_SUMMARY,
    ),
    ("1981_15_NYJ_SF", "nfl-matt-bahr"): (
        {
            "date": "1981-12-12",
            "season": "1981",
            "week": "15",
            "season_type": "REG",
            "game_id": "1981_15_NYJ_CLE",
            "player_id": "nfl-matt-bahr",
            "player_name": "Matt Bahr",
            "team": "CLE",
            "opponent": "NYJ",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "26,20",
        },
        NFL_1981_ANNUAL_SUMMARY,
    ),
    ("1990_06_LA_NYJ", "nfl-john-carney"): (
        {
            "date": "1990-10-14",
            "season": "1990",
            "week": "6",
            "season_type": "REG",
            "game_id": "1990_06_SD_NYJ",
            "player_id": "nfl-john-carney",
            "player_name": "John Carney",
            "team": "SD",
            "opponent": "NYJ",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "3",
            "fg_attempts": "3",
            "fg_made_distances": "34,42,37",
        },
        NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1990_08_TB_LA", "nfl-john-carney"): (
        {
            "date": "1990-10-28",
            "season": "1990",
            "week": "8",
            "season_type": "REG",
            "game_id": "1990_08_TB_SD",
            "player_id": "nfl-john-carney",
            "player_name": "John Carney",
            "team": "SD",
            "opponent": "TB",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "28,27",
        },
        NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1990_10_DEN_LA", "nfl-john-carney"): (
        {
            "date": "1990-11-11",
            "season": "1990",
            "week": "10",
            "season_type": "REG",
            "game_id": "1990_10_DEN_SD",
            "player_id": "nfl-john-carney",
            "player_name": "John Carney",
            "team": "SD",
            "opponent": "DEN",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "4",
            "fg_attempts": "4",
            "fg_made_distances": "19,23,43,32",
        },
        NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1988_05_HOU_DAL", "nfl-luis-zendejas"): (
        {
            "date": "1988-10-02",
            "season": "1988",
            "week": "5",
            "season_type": "REG",
            "game_id": "1988_05_HOU_PHI",
            "player_id": "nfl-luis-zendejas",
            "player_name": "Luis Zendejas",
            "team": "PHI",
            "opponent": "HOU",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "3",
            "fg_attempts": "3",
            "fg_made_distances": "22,39,41",
        },
        NFL_1988_ANNUAL_SUMMARY,
    ),
    ("1988_10_LA_DAL", "nfl-luis-zendejas"): (
        {
            "date": "1988-11-06",
            "season": "1988",
            "week": "10",
            "season_type": "REG",
            "game_id": "1988_10_LA_PHI",
            "player_id": "nfl-luis-zendejas",
            "player_name": "Luis Zendejas",
            "team": "PHI",
            "opponent": "LA",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "3",
            "fg_attempts": "3",
            "fg_made_distances": "23,50,40",
        },
        NFL_1988_ANNUAL_SUMMARY,
    ),
    ("1988_11_DAL_PIT", "nfl-luis-zendejas"): (
        {
            "date": "1988-11-13",
            "season": "1988",
            "week": "11",
            "season_type": "REG",
            "game_id": "1988_11_PHI_PIT",
            "player_id": "nfl-luis-zendejas",
            "player_name": "Luis Zendejas",
            "team": "PHI",
            "opponent": "PIT",
            "xp_made": "3",
            "xp_attempts": "3",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "34,18",
        },
        NFL_1988_ANNUAL_SUMMARY,
    ),
    ("1988_14_WAS_DAL", "nfl-luis-zendejas"): (
        {
            "date": "1988-12-04",
            "season": "1988",
            "week": "14",
            "season_type": "REG",
            "game_id": "1988_14_WAS_PHI",
            "player_id": "nfl-luis-zendejas",
            "player_name": "Luis Zendejas",
            "team": "PHI",
            "opponent": "WAS",
            "xp_made": "1",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "40,19",
        },
        NFL_1988_ANNUAL_SUMMARY,
    ),
    ("1989_10_PHI_PHX", "nfl-luis-zendejas"): (
        {
            "date": "1989-11-12",
            "season": "1989",
            "week": "10",
            "season_type": "REG",
            "game_id": "1989_10_DAL_PHX",
            "player_id": "nfl-luis-zendejas",
            "player_name": "Luis Zendejas",
            "team": "DAL",
            "opponent": "PHX",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "32,29",
        },
        NFL_1989_ANNUAL_SUMMARY,
    ),
    ("1990_12_CHI_SD", "nfl-fuad-reveiz"): (
        {
            "date": "1990-11-25",
            "season": "1990",
            "week": "12",
            "season_type": "REG",
            "game_id": "1990_12_CHI_MIN",
            "player_id": "nfl-fuad-reveiz",
            "player_name": "Fuad Reveiz",
            "team": "MIN",
            "opponent": "CHI",
            "xp_made": "5",
            "xp_attempts": "5",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "41,45",
        },
        NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1990_13_GB_SD", "nfl-fuad-reveiz"): (
        {
            "date": "1990-12-02",
            "season": "1990",
            "week": "13",
            "season_type": "REG",
            "game_id": "1990_13_GB_MIN",
            "player_id": "nfl-fuad-reveiz",
            "player_name": "Fuad Reveiz",
            "team": "MIN",
            "opponent": "GB",
            "xp_made": "2",
            "xp_attempts": "2",
            "fg_made": "3",
            "fg_attempts": "3",
            "fg_made_distances": "29,32,41",
        },
        NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1990_14_SD_NYG", "nfl-fuad-reveiz"): (
        {
            "date": "1990-12-09",
            "season": "1990",
            "week": "14",
            "season_type": "REG",
            "game_id": "1990_14_MIN_NYG",
            "player_id": "nfl-fuad-reveiz",
            "player_name": "Fuad Reveiz",
            "team": "MIN",
            "opponent": "NYG",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "22,37",
        },
        NFL_1990_ANNUAL_SUMMARY,
    ),
    ("1995_13_CAR_SF", "nfl-doug-brien"): (
        {
            "date": "1995-11-26",
            "season": "1995",
            "week": "13",
            "season_type": "REG",
            "game_id": "1995_13_CAR_NO",
            "player_id": "nfl-doug-brien",
            "player_name": "Doug Brien",
            "team": "NO",
            "opponent": "CAR",
            "xp_made": "4",
            "xp_attempts": "4",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "45,39",
        },
        NFL_1995_ANNUAL_SUMMARY,
    ),
    ("1995_17_SF_NYJ", "nfl-doug-brien"): (
        {
            "date": "1995-12-24",
            "season": "1995",
            "week": "17",
            "season_type": "REG",
            "game_id": "1995_17_NO_NYJ",
            "player_id": "nfl-doug-brien",
            "player_name": "Doug Brien",
            "team": "NO",
            "opponent": "NYJ",
            "xp_made": "0",
            "xp_attempts": "0",
            "fg_made": "2",
            "fg_attempts": "4",
            "fg_made_distances": "32,23",
        },
        NFL_1995_ANNUAL_SUMMARY,
    ),
    ("1997_06_MIN_OAK", "nfl-greg-davis"): (
        {
            "date": "1997-10-05",
            "season": "1997",
            "week": "6",
            "season_type": "REG",
            "game_id": "1997_06_SD_OAK",
            "player_id": "nfl-greg-davis",
            "player_name": "Greg Davis",
            "team": "SD",
            "opponent": "OAK",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "6",
            "fg_attempts": "6",
            "fg_made_distances": "30,22,38,43,33,33",
        },
        NFL_1997_ANNUAL_SUMMARY,
    ),
    ("1997_09_IND_MIN", "nfl-greg-davis"): (
        {
            "date": "1997-10-26",
            "season": "1997",
            "week": "9",
            "season_type": "REG",
            "game_id": "1997_09_IND_SD",
            "player_id": "nfl-greg-davis",
            "player_name": "Greg Davis",
            "team": "SD",
            "opponent": "IND",
            "xp_made": "2",
            "xp_attempts": "3",
            "fg_made": "5",
            "fg_attempts": "6",
            "fg_made_distances": "45,35,34,31,45",
        },
        NFL_1997_ANNUAL_SUMMARY,
    ),
    ("1997_12_OAK_MIN", "nfl-greg-davis"): (
        {
            "date": "1997-11-16",
            "season": "1997",
            "week": "12",
            "season_type": "REG",
            "game_id": "1997_12_OAK_SD",
            "player_id": "nfl-greg-davis",
            "player_name": "Greg Davis",
            "team": "SD",
            "opponent": "OAK",
            "xp_made": "1",
            "xp_attempts": "1",
            "fg_made": "2",
            "fg_attempts": "3",
            "fg_made_distances": "45,22",
        },
        NFL_1997_ANNUAL_SUMMARY,
    ),
    ("1976_08_DEN_DET", "nfl-errol-mann"): (
        {
            "date": "1976-10-31",
            "season": "1976",
            "week": "8",
            "season_type": "REG",
            "game_id": "1976_08_DEN_OAK",
            "player_id": "nfl-errol-mann",
            "player_name": "Errol Mann",
            "team": "OAK",
            "opponent": "DEN",
            "xp_made": "1",
            "xp_attempts": "2",
            "fg_made": "2",
            "fg_attempts": "2",
            "fg_made_distances": "23,36",
        },
        "https://www.pro-football-reference.com/boxscores/197610310rai.htm; corroborated_by=" + NFL_1976_ANNUAL_SUMMARY,
    ),
    ("1983_07_SD_BUF", "nfl-fred-steinfort"): (
        {
            "date": "1983-10-16",
            "season": "1983",
            "week": "7",
            "season_type": "REG",
            "game_id": "1983_07_SD_NE",
            "player_id": "nfl-fred-steinfort",
            "player_name": "Fred Steinfort",
            "team": "NE",
            "opponent": "SD",
            "xp_made": "4",
            "xp_attempts": "4",
            "fg_made": "3",
            "fg_attempts": "3",
            "fg_made_distances": "35,20,32",
        },
        "https://www.pro-football-reference.com/boxscores/198310160nwe.htm; corroborated_by=" + NFL_1983_ANNUAL_SUMMARY,
    ),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    upload_rows = read_rows(UPLOAD_IN)
    resolved = read_rows(RESOLVED_OUT)
    unresolved = read_rows(UNRESOLVED_OUT)
    resolved_keys = {(row["game_id"], row["player_id"]) for row in resolved}

    remaining: list[dict[str, str]] = []
    added = 0
    for row in unresolved:
        key = (row["game_id"], row["player_id"])
        if key in resolved_keys:
            continue
        external = VERIFIED_EXTERNAL_ROWS.get(key)
        if external:
            distances, source_url = external
            if len(distances) != int(row["fg_made"]):
                remaining.append({**row, "unresolved_reason": "external verification failed count check"})
                continue
            out = {col: row[col] for col in gsis.CSV_COLUMNS if col != "fg_made_distances"}
            out["fg_made_distances"] = ",".join(str(distance) for distance in distances)
            out["gsis_url"] = source_url
            resolved.append(out)
            resolved_keys.add(key)
            added += 1
            continue
        corrected = VERIFIED_CORRECTED_ROWS.get(key)
        if corrected:
            corrected_row, source_url = corrected
            corrected_key = (corrected_row["game_id"], corrected_row["player_id"])
            if corrected_key in resolved_keys:
                continue
            distances = [int(value) for value in corrected_row["fg_made_distances"].split(",") if value]
            if (
                len(distances) != int(corrected_row["fg_made"])
                or max(distances) != int(row["long_made_fg"])
            ):
                remaining.append({**row, "unresolved_reason": "corrected club/annual verification failed count/long check"})
                continue
            resolved.append({**corrected_row, "gsis_url": source_url})
            resolved_keys.add(corrected_key)
            added += 1
            continue
        verified = VERIFIED_DISTANCES.get(key)
        if not verified or key in resolved_keys:
            remaining.append(row)
            continue
        distances, source_url = verified
        if len(distances) != int(row["fg_made"]) or max(distances) != int(row["long_made_fg"]):
            remaining.append({**row, "unresolved_reason": "club media-guide verification failed count/long check"})
            continue
        out = {col: row[col] for col in gsis.CSV_COLUMNS if col != "fg_made_distances"}
        out["fg_made_distances"] = ",".join(str(distance) for distance in distances)
        out["gsis_url"] = source_url
        resolved.append(out)
        resolved_keys.add(key)
        added += 1

    gsis.flush_outputs(upload_rows, resolved, remaining)
    print(f"club media-guide rows added: {added}")
    print(f"resolved multi-FG rows: {len(resolved)}")
    print(f"unresolved multi-FG rows: {len(remaining)}")


if __name__ == "__main__":
    main()
