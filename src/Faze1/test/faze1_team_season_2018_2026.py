import re
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Linux NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

years = range(2018, 2027)

teams = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BRK": "Brooklyn Nets",
    "CHO": "Charlotte Hornets",
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards"
}

def extract_between(text, start, end):
    pattern = re.compile(re.escape(start) + r"\s*(.*?)\s*" + re.escape(end), re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""

rows = []

for year in years:
    print(f"\n===== Season {year} =====")

    league_url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
    r = requests.get(league_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    champion = extract_between(page_text, "League Champion:", "Most Valuable Player:")
    mvp = extract_between(page_text, "Most Valuable Player:", "Rookie of the Year:")
    roy = extract_between(page_text, "Rookie of the Year:", "PPG Leader:")
    ppg_leader = extract_between(page_text, "PPG Leader:", "RPG Leader:")
    rpg_leader = extract_between(page_text, "RPG Leader:", "APG Leader:")
    apg_leader = extract_between(page_text, "APG Leader:", "WS Leader:")
    ws_leader = extract_between(page_text, "WS Leader:", "More league info")

    east = {}
    west = {}
    for table in soup.find_all("table"):
        if table.get("id") == "confs_standings_E":
            tbody = table.find("tbody")
            for tr in tbody.find_all("tr"):
                team = tr.find("th").text.strip("*")
                tds = [x.text for x in tr.find_all("td")]
                east[team] = tds
        if table.get("id") == "confs_standings_W":
            tbody = table.find("tbody")
            for tr in tbody.find_all("tr"):
                team = tr.find("th").text.strip("*")
                tds = [x.text for x in tr.find_all("td")]
                west[team] = tds

    for code, name in teams.items():
        print(f"  Extractng {name}...")
        url = f"https://www.basketball-reference.com/teams/{code}/{year}.html"
        try:
            rr = requests.get(url, headers=headers, timeout=10)
            if rr.status_code != 200:
                print(f"    Skipping {name} (status {rr.status_code})")
                continue
        except Exception as e:
            print(f"    Error fetching {name}: {e}")
            continue

        ss = BeautifulSoup(rr.text, "html.parser")
        info_div = ss.find("div", id="info")
        info_text = info_div.get_text(" ", strip=True) if info_div else ss.get_text(" ", strip=True)

        record = extract_between(info_text, "Record:", "Coach:")
        coach = extract_between(info_text, "Coach:", "Executive:")
        executive = extract_between(info_text, "Executive:", "PTS/G:")
        pts = extract_between(info_text, "PTS/G:", "Opp PTS/G:")
        opp_pts = extract_between(info_text, "Opp PTS/G:", "SRS:")
        srs = extract_between(info_text, "SRS:", "Pace:")
        pace = extract_between(info_text, "Pace:", "Off Rtg:")
        off_rtg = extract_between(info_text, "Off Rtg:", "Def Rtg:")
        def_rtg = extract_between(info_text, "Def Rtg:", "Net Rtg:")
        net_rtg = extract_between(info_text, "Net Rtg:", "Expected W-L:")
        expected = extract_between(info_text, "Expected W-L:", "Preseason Odds:")
        odds = extract_between(info_text, "Preseason Odds:", "Arena:")
        arena = extract_between(info_text, "Arena:", "Attendance:")
        attendance = extract_between(info_text, "Attendance:", "Playoffs:")
        playoffs = extract_between(info_text, "Playoffs:", "")

        conf = ""
        W = L = WL = GB = PSG = PAG = SRS_CONF = ""
        if name in east:
            conf = "East"
            data = east[name]
            if len(data) >= 7:
                W, L, WL, GB, PSG, PAG, SRS_CONF = data[:7]
        elif name in west:
            conf = "West"
            data = west[name]
            if len(data) >= 7:
                W, L, WL, GB, PSG, PAG, SRS_CONF = data[:7]

        rows.append({
            "Season": year,
            "Conference": conf,
            "Team": name,
            "League Champion": champion,
            "MVP": mvp,
            "ROY": roy,
            "PPG Leader": ppg_leader,
            "RPG Leader": rpg_leader,
            "APG Leader": apg_leader,
            "WS Leader": ws_leader,
            "Conference Wins": W,
            "Conference Losses": L,
            "Conference W/L%": WL,
            "GB": GB,
            "PS/G": PSG,
            "PA/G": PAG,
            "Conference SRS": SRS_CONF,
            "Record": record,
            "Coach": coach,
            "Executive": executive,
            "Team PTS/G": pts,
            "Opponent PTS/G": opp_pts,
            "SRS": srs,
            "Pace": pace,
            "Offensive Rating": off_rtg,
            "Defensive Rating": def_rtg,
            "Net Rating": net_rtg,
            "Expected W-L": expected,
            "Preseason Odds": odds,
            "Arena": arena,
            "Attendance": attendance,
            "Playoffs": playoffs
        })

        time.sleep(random.randint(1, 3))

df = pd.DataFrame(rows)
df.to_csv("NBA_2018_2026.csv", index=False, encoding="utf-8-sig")
print("\n CSV ba etelaate kamel save shod.")
