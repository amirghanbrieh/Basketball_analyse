import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0"
}

years = range(2018, 2027)

teams = {
    "ATL":"Atlanta Hawks",
    "BOS":"Boston Celtics",
    "BRK":"Brooklyn Nets",
    "CHO":"Charlotte Hornets",
    "CHI":"Chicago Bulls",
    "CLE":"Cleveland Cavaliers",
    "DAL":"Dallas Mavericks",
    "DEN":"Denver Nuggets",
    "DET":"Detroit Pistons",
    "GSW":"Golden State Warriors",
    "HOU":"Houston Rockets",
    "IND":"Indiana Pacers",
    "LAC":"Los Angeles Clippers",
    "LAL":"Los Angeles Lakers",
    "MEM":"Memphis Grizzlies",
    "MIA":"Miami Heat",
    "MIL":"Milwaukee Bucks",
    "MIN":"Minnesota Timberwolves",
    "NOP":"New Orleans Pelicans",
    "NYK":"New York Knicks",
    "OKC":"Oklahoma City Thunder",
    "ORL":"Orlando Magic",
    "PHI":"Philadelphia 76ers",
    "PHO":"Phoenix Suns",
    "POR":"Portland Trail Blazers",
    "SAC":"Sacramento Kings",
    "SAS":"San Antonio Spurs",
    "TOR":"Toronto Raptors",
    "UTA":"Utah Jazz",
    "WAS":"Washington Wizards"
}

rows = []

for year in years:

    print(year)

    league_url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"

    r = requests.get(league_url, headers=headers)

    soup = BeautifulSoup(r.text,"html.parser")

    text = soup.get_text(" ", strip=True)

    champion = ""
    mvp = ""
    roy = ""
    ppg = ""
    rpg = ""
    apg = ""
    ws = ""

    m = re.search(r"League Champion:\s*(.*?)\s*Most Valuable Player:",text)
    if m:
        champion = m.group(1)

    m = re.search(r"Most Valuable Player:\s*(.*?)\s*Rookie of the Year:",text)
    if m:
        mvp = m.group(1)

    m = re.search(r"Rookie of the Year:\s*(.*?)\s*PPG Leader:",text)
    if m:
        roy = m.group(1)

    m = re.search(r"PPG Leader:\s*(.*?)\s*RPG Leader:",text)
    if m:
        ppg = m.group(1)

    m = re.search(r"RPG Leader:\s*(.*?)\s*APG Leader:",text)
    if m:
        rpg = m.group(1)

    m = re.search(r"APG Leader:\s*(.*?)\s*WS Leader:",text)
    if m:
        apg = m.group(1)

    m = re.search(r"WS Leader:\s*(.*?)\s*More league info",text)
    if m:
        ws = m.group(1)

    east = {}
    west = {}

    for table in soup.find_all("table"):

        if table.get("id")=="confs_standings_E":

            tbody=table.find("tbody")

            for tr in tbody.find_all("tr"):

                team=tr.find("th").text.strip("*")

                tds=[x.text for x in tr.find_all("td")]

                east[team]=tds

        if table.get("id")=="confs_standings_W":

            tbody=table.find("tbody")

            for tr in tbody.find_all("tr"):

                team=tr.find("th").text.strip("*")

                tds=[x.text for x in tr.find_all("td")]

                west[team]=tds

    for code,name in teams.items():

        print(name)

        url=f"https://www.basketball-reference.com/teams/{code}/{year}.html"

        rr=requests.get(url,headers=headers)

        if rr.status_code!=200:
            continue

        ss=BeautifulSoup(rr.text,"html.parser")

        txt=ss.get_text(" ",strip=True)

        coach=""
        executive=""
        record=""
        pts=""
        opppts=""
        srs=""
        pace=""
        offrtg=""
        defrtg=""
        netrtg=""
        expected=""
        odds=""
        arena=""
        attendance=""
        playoffs=""

        x=re.search(r"Record:\s*(.*?)\s*Coach:",txt)
        if x: record=x.group(1)

        x=re.search(r"Coach:\s*(.*?)\s*Executive:",txt)
        if x: coach=x.group(1)

        x=re.search(r"Executive:\s*(.*?)\s*PTS/G:",txt)
        if x: executive=x.group(1)

        x=re.search(r"PTS/G:\s*(.*?)\s*Opp PTS/G:",txt)
        if x: pts=x.group(1)

        x=re.search(r"Opp PTS/G:\s*(.*?)\s*SRS:",txt)
        if x: opppts=x.group(1)

        x=re.search(r"SRS:\s*(.*?)\s*Pace:",txt)
        if x: srs=x.group(1)

        x=re.search(r"Pace:\s*(.*?)\s*Off Rtg:",txt)
        if x: pace=x.group(1)

        x=re.search(r"Off Rtg:\s*(.*?)\s*Def Rtg:",txt)
        if x: offrtg=x.group(1)

        x=re.search(r"Def Rtg:\s*(.*?)\s*Net Rtg:",txt)
        if x: defrtg=x.group(1)

        x=re.search(r"Net Rtg:\s*(.*?)\s*Expected W-L:",txt)
        if x: netrtg=x.group(1)

        x=re.search(r"Expected W-L:\s*(.*?)\s*Preseason Odds:",txt)
        if x: expected=x.group(1)

        x=re.search(r"Preseason Odds:\s*(.*?)\s*Arena:",txt)
        if x: odds=x.group(1)

        x=re.search(r"Arena:\s*(.*?)\s*Attendance:",txt)
        if x: arena=x.group(1)

        x=re.search(r"Attendance:\s*(.*?)\s*NBA",txt)
        if x: attendance=x.group(1)

        x=re.search(r"Playoffs:\s*(.*)",txt)
        if x: playoffs=x.group(1)

        conf=""

        W=L=WL=GB=PSG=PAG=SRS_CONF=""

        if name in east:

            conf="East"

            data=east[name]

            W,L,WL,GB,PSG,PAG,SRS_CONF=data[:7]

        elif name in west:

            conf="West"

            data=west[name]

            W,L,WL,GB,PSG,PAG,SRS_CONF=data[:7]

        rows.append({

            "Season":year,

            "Conference":conf,

            "Team":name,

            "League Champion":champion,

            "MVP":mvp,

            "ROY":roy,

            "PPG Leader":ppg,

            "RPG Leader":rpg,

            "APG Leader":apg,

            "WS Leader":ws,

            "Conference Wins":W,

            "Conference Losses":L,

            "Conference W/L%":WL,

            "GB":GB,

            "PS/G":PSG,

            "PA/G":PAG,

            "Conference SRS":SRS_CONF,

            "Record":record,

            "Coach":coach,

            "Executive":executive,

            "Team PTS/G":pts,

            "Opponent PTS/G":opppts,

            "SRS":srs,

            "Pace":pace,

            "Offensive Rating":offrtg,

            "Defensive Rating":defrtg,

            "Net Rating":netrtg,

            "Expected W-L":expected,

            "Preseason Odds":odds,

            "Arena":arena,

            "Attendance":attendance,

            "Playoffs":playoffs

        })

        time.sleep(1)

df=pd.DataFrame(rows)

df.to_csv("NBA_2018_2026.csv",index=False,encoding="utf-8-sig")

print(df.head())

print("Saved NBA_2018_2026.csv")
