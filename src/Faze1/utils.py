import os
import re
import csv
import time
import random
from datetime import datetime
from typing import Optional, List, Dict, Any
from io import StringIO

import requests
import pandas as pd
from bs4 import BeautifulSoup


class BaseScraper:
    """Base class for handling HTTP requests."""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Linux NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def __init__(self, timeout: int = 20, delay: float = 1.0):
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Send a GET request with error handling and delay."""
        try:
            time.sleep(self.delay)
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and return a BeautifulSoup object."""
        resp = self._get(url)
        return BeautifulSoup(resp.text, 'html.parser') if resp else None

    @staticmethod
    def _extract_between(text: str, start: str, end: str) -> str:
        """Extract text between two given markers."""
        pattern = re.compile(re.escape(start) + r"\s*(.*?)\s*" + re.escape(end), re.DOTALL)
        match = pattern.search(text)
        return match.group(1).strip() if match else ""


class SeasonScraper(BaseScraper):

    LABEL_MAP = {
        "League Champion": "Champion",
        "Most Valuable Player": "MVP",
        "Rookie of the Year": "ROY",
        "PPG Leader": "PPG_Leader",
        "RPG Leader": "RPG_Leader",
        "APG Leader": "APG_Leader",
        "WS Leader": "WS_Leader"
    }

    def scrape_season(self, season_end_year: int) -> Optional[Dict[str, Any]]:
        url = f'https://www.basketball-reference.com/leagues/NBA_{season_end_year}.html'
        soup = self._soup(url)
        if not soup:
            return None

        data = {
            'Season': f"{season_end_year-1}-{season_end_year}",
            'Champion': None,
            'MVP': None,
            'ROY': None,
            'PPG_Leader': None,
            'RPG_Leader': None,
            'APG_Leader': None,
            'WS_Leader': None
        }

        for p in soup.find_all('p'):
            strong = p.find('strong')
            if strong:
                strong_text = strong.get_text(strip=True).replace(':', '')
                if strong_text in self.LABEL_MAP:
                    full_text = p.get_text(separator=' ', strip=True)
                    if ':' in full_text:
                        value = full_text.split(':', 1)[1].strip()
                        data[self.LABEL_MAP[strong_text]] = value

        return data

    def scrape_range(self, start_year: int, end_year: int) -> List[Dict]:
        results = []
        for year in range(start_year, end_year + 1):
            print(f"Processing season {year-1}-{year}")
            data = self.scrape_season(year)
            if data:
                results.append(data)
            time.sleep(self.delay)
        return results


class ActivePlayersScraper(BaseScraper):
    """Scrape the list of active players from the player pages."""

    def scrape(self) -> List[Dict]:
        base_url = 'https://www.basketball-reference.com/players/'
        letters = 'abcdefghijklmnopqrstuvwxyz'
        all_players = []

        for letter in letters:
            url = f'{base_url}{letter}/'
            print(f"Searching in {url} ...")
            soup = self._soup(url)
            if not soup:
                continue

            table = soup.find('table')
            if not table:
                print(f"No table for letter {letter}")
                continue

            for row in table.find_all('tr'):
                player_link = row.find('a')
                if not player_link:
                    continue

                # Active players are marked with <strong> around their name
                is_active = (
                    (player_link.parent and player_link.parent.name == 'strong') or
                    (row.find('strong') is not None)
                )
                if not is_active:
                    continue

                cols = row.find_all(['td', 'th'])
                if len(cols) < 7:
                    continue

                player_name = player_link.get_text(strip=True)
                player_url = 'https://www.basketball-reference.com' + player_link.get('href', '')
                player_id = player_url.split('/')[-1].replace('.html', '')

                all_players.append({
                    'PlayerID': player_id,
                    'PlayerName': player_name,
                    'PlayerURL': player_url,
                    'From': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                    'To': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                    'Pos': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                    'Ht': cols[4].get_text(strip=True) if len(cols) > 4 else '',
                    'Wt': cols[5].get_text(strip=True) if len(cols) > 5 else '',
                    'BirthDate': cols[6].get_text(strip=True) if len(cols) > 6 else '',
                    'College': cols[7].get_text(strip=True) if len(cols) > 7 else ''
                })

            print(f"Found {len([p for p in all_players if p['PlayerID'].startswith(letter)])} active players for {letter}")
            time.sleep(self.delay)

        return all_players


class TeamsSummaryScraper(BaseScraper):
    """extract links to each team's page."""

    def scrape(self):
        url = 'https://www.basketball-reference.com/teams/'
        soup = self._soup(url)
        if not soup:
            return pd.DataFrame(), []

        # Find the table with "Active Franchises"
        table = None
        for h in soup.find_all(['h2', 'h3']):
            if 'Active Franchises' in h.get_text():
                table = h.find_next('table')
                break

        if not table:
            # Fallback: use pandas read_html
            try:
                dfs = pd.read_html(url, header=0)
                for df in dfs:
                    if 'Franchise' in df.columns or 'Lg' in df.columns:
                        table_df = df
                        break
                else:
                    raise Exception('Teams table not found.')
            except Exception:
                return pd.DataFrame(), []
        else:
            table_df = pd.read_html(StringIO(str(table)))[0]

        cols = ['Franchise', 'Lg', 'From', 'To', 'Yrs', 'G', 'W', 'L',
                'W/L%', 'Plyfs', 'Div', 'Conf', 'Champ']
        existing_cols = [c for c in cols if c in table_df.columns]
        summary_df = table_df[existing_cols].copy()

        # Extract team links
        team_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/teams/') and re.match(r'^/teams/[A-Z]{2,3}/$', href):
                full_url = 'https://www.basketball-reference.com' + href
                if full_url not in team_links:
                    team_links.append(full_url)

        return summary_df, team_links


class TeamSeasonScraper(BaseScraper):

    TEAMS = {
        "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BRK": "Brooklyn Nets",
        "CHO": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
        "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
        "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
        "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
        "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
        "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
        "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHO": "Phoenix Suns",
        "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
        "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards"
    }

    def scrape_season(self, year: int) -> List[Dict]:
        rows = []
        league_url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
        soup = self._soup(league_url)
        if not soup:
            return rows

        page_text = soup.get_text(" ", strip=True)

        champion = self._extract_between(page_text, "League Champion:", "Most Valuable Player:")
        mvp = self._extract_between(page_text, "Most Valuable Player:", "Rookie of the Year:")
        roy = self._extract_between(page_text, "Rookie of the Year:", "PPG Leader:")
        ppg_leader = self._extract_between(page_text, "PPG Leader:", "RPG Leader:")
        rpg_leader = self._extract_between(page_text, "RPG Leader:", "APG Leader:")
        apg_leader = self._extract_between(page_text, "APG Leader:", "WS Leader:")
        ws_leader = self._extract_between(page_text, "WS Leader:", "More league info")

        # tables data extractore
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

        for code, name in self.TEAMS.items():
            print(f"Extracting {name} ({year})...")
            url = f"https://www.basketball-reference.com/teams/{code}/{year}.html"
            soup_team = self._soup(url)
            if not soup_team:
                continue

            info_div = soup_team.find("div", id="info")
            info_text = info_div.get_text(" ", strip=True) if info_div else soup_team.get_text(" ", strip=True)

            record = self._extract_between(info_text, "Record:", "Coach:")
            coach = self._extract_between(info_text, "Coach:", "Executive:")
            executive = self._extract_between(info_text, "Executive:", "PTS/G:")
            pts = self._extract_between(info_text, "PTS/G:", "Opp PTS/G:")
            opp_pts = self._extract_between(info_text, "Opp PTS/G:", "SRS:")
            srs = self._extract_between(info_text, "SRS:", "Pace:")
            pace = self._extract_between(info_text, "Pace:", "Off Rtg:")
            off_rtg = self._extract_between(info_text, "Off Rtg:", "Def Rtg:")
            def_rtg = self._extract_between(info_text, "Def Rtg:", "Net Rtg:")
            net_rtg = self._extract_between(info_text, "Net Rtg:", "Expected W-L:")
            expected = self._extract_between(info_text, "Expected W-L:", "Preseason Odds:")
            odds = self._extract_between(info_text, "Preseason Odds:", "Arena:")
            arena = self._extract_between(info_text, "Arena:", "Attendance:")
            attendance = self._extract_between(info_text, "Attendance:", "Playoffs:")
            playoffs = self._extract_between(info_text, "Playoffs:", "")

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

            time.sleep(random.uniform(1, 3))

        return rows

    def scrape_range(self, start_year: int, end_year: int) -> List[Dict]:
        all_rows = []
        for year in range(start_year, end_year + 1):
            print(f"\n===== Season {year} =====")
            all_rows.extend(self.scrape_season(year))
        return all_rows


class PlayerStatsScraper(BaseScraper):
    """player and team stats per season, and add rankings."""

    def _get_team_details(self, team_url: str) -> Dict:
        """Get coach, arena, attendance, and top players from team page."""
        if not team_url:
            return {'coach': '', 'arena': '', 'attendance': '', 'top_players': ''}
        if not team_url.startswith('http'):
            team_url = f"https://www.basketball-reference.com{team_url}"

        soup = self._soup(team_url)
        if not soup:
            return {'coach': '', 'arena': '', 'attendance': '', 'top_players': ''}

        info_div = soup.find('div', id='info')
        coach = arena = attendance = ''
        if info_div:
            text = info_div.get_text()
            coach_match = re.search(r'Coach:\s*([^,]+)', text)
            coach = coach_match.group(1).strip() if coach_match else ''
            arena_match = re.search(r'Arena:\s*([^,]+)', text)
            arena = arena_match.group(1).strip() if arena_match else ''
            att_match = re.search(r'Attendance:\s*([\d,]+)', text)
            attendance = att_match.group(1).replace(',', '') if att_match else ''

        top_players = []
        roster = soup.find('table', {'id': 'roster'})
        if roster:
            tbody = roster.find('tbody')
            if tbody:
                for row in tbody.find_all('tr')[:7]:
                    name_tag = row.find('a')
                    if name_tag:
                        top_players.append(name_tag.get_text(strip=True))

        return {
            'coach': coach,
            'arena': arena,
            'attendance': attendance,
            'top_players': ', '.join(top_players)
        }

    def scrape_teams_season(self, year: int) -> List[Dict]:
        """team standings data for a given season."""
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
        soup = self._soup(url)
        if not soup:
            return []

        tables = []
        for table_id in ['confs_standings_E', 'confs_standings_W']:
            table = soup.find('table', {'id': table_id})
            if table:
                tables.append(table)

        if not tables:
            # Fallback: try to find standings table
            standings_div = soup.find('div', id='all_standings')
            if standings_div:
                table = standings_div.find('table')
                if table:
                    tables.append(table)
            else:
                table = soup.find('table', {'class': 'stats_table'})
                if table:
                    tables.append(table)

        if not tables:
            return []

        teams = []
        for table in tables:
            tbody = table.find('tbody')
            if not tbody:
                continue
            for row in tbody.find_all('tr'):
                if row.get('class') and 'thead' in row.get('class'):
                    continue
                cols = row.find_all('td')
                if len(cols) < 9:
                    continue

                first_col = row.find('th') if row.find('th') else cols[0]
                team_link = first_col.find('a') if first_col else None
                if not team_link:
                    continue

                team_name = team_link.get_text(strip=True)
                team_url = team_link.get('href')

                record = cols[0].get_text(strip=True) if len(cols) > 0 else ''
                wins, losses = record.split('-') if '-' in record else ('', '')
                win_loss_pct = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                gb = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                pts_g = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                opp_pts_g = cols[4].get_text(strip=True) if len(cols) > 4 else ''
                srs = cols[5].get_text(strip=True) if len(cols) > 5 else ''

                details = self._get_team_details(team_url)

                teams.append({
                    'season': f"{year-1}-{str(year)[-2:]}",
                    'season_year': year,
                    'team': team_name,
                    'wins': wins,
                    'losses': losses,
                    'win_loss_pct': win_loss_pct,
                    'games_behind': gb,
                    'pts_per_game': pts_g,
                    'opp_pts_per_game': opp_pts_g,
                    'srs': srs,
                    'coach': details['coach'],
                    'arena': details['arena'],
                    'attendance': details['attendance'],
                    'top_players': details['top_players']
                })
                time.sleep(0.3)

        return teams

    def scrape_players_season(self, year: int) -> Optional[pd.DataFrame]:
        """player totals for a given season."""
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}_totals.html"
        soup = self._soup(url)
        if not soup:
            return None

        table = soup.find('table', {'id': 'totals_stats'})
        if not table:
            return None

        thead = table.find('thead')
        if not thead:
            return None

        header_rows = thead.find_all('tr')
        headers = [th.get_text(strip=True) for th in header_rows[-1].find_all('th')]

        data = []
        tbody = table.find('tbody')
        if not tbody:
            return None

        for tr in tbody.find_all('tr'):
            if tr.get('class') and 'thead' in tr.get('class'):
                continue

            row_data = {}
            tds = tr.find_all('td')
            if not tds:
                continue

            th = tr.find('th')
            row_data['Rk'] = th.get_text(strip=True) if th else ''

            for i, td in enumerate(tds):
                col_name = headers[i + 1] if i + 1 < len(headers) else f'col_{i}'
                a = td.find('a')
                if a and col_name in ['Player', 'player']:
                    row_data[col_name] = a.get_text(strip=True)
                else:
                    text = td.get_text(strip=True)
                    if text and text.replace('.', '').replace('-', '').isdigit():
                        text = text.replace(',', '')
                    row_data[col_name] = text

            if row_data.get('Player') and row_data['Player'] != 'Player':
                row_data['Season'] = f"{year-1}-{year}"
                row_data['Season_Year'] = year
                data.append(row_data)

        return pd.DataFrame(data) if data else None

    @staticmethod
    def add_player_rankings(df: pd.DataFrame) -> pd.DataFrame:
        """Add ranking columns for various stats."""
        if df is None or df.empty:
            return df

        stat_cols = ['PTS', 'TRB', 'AST', 'STL', 'BLK', 'FG', 'FGA', '3P', '3PA',
                     'FT', 'FTA', 'ORB', 'DRB', 'TOV', 'PF', 'MP']
        for col in stat_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        higher_better = ['PTS', 'TRB', 'AST', 'STL', 'BLK', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB', 'MP']
        lower_better = ['TOV', 'PF']

        for col in higher_better:
            if col in df.columns:
                rank_col = f'{col}_Rank'
                df[rank_col] = df.groupby('Season_Year')[col].rank(method='min', ascending=False).astype('Int64')

        for col in lower_better:
            if col in df.columns:
                rank_col = f'{col}_Rank'
                df[rank_col] = df.groupby('Season_Year')[col].rank(method='min', ascending=True).astype('Int64')

        if all(c in df.columns for c in ['PTS', 'TRB', 'AST']):
            df['PTS_Norm'] = df.groupby('Season_Year')['PTS'].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0
            )
            df['TRB_Norm'] = df.groupby('Season_Year')['TRB'].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0
            )
            df['AST_Norm'] = df.groupby('Season_Year')['AST'].transform(
                lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0
            )
            df['Combined_Score'] = df['PTS_Norm'] * 0.4 + df['TRB_Norm'] * 0.3 + df['AST_Norm'] * 0.3
            df['Overall_Rank'] = df.groupby('Season_Year')['Combined_Score'].rank(method='min', ascending=False).astype('Int64')

        return df

    @staticmethod
    def add_team_rankings(df: pd.DataFrame) -> pd.DataFrame:
        """Add ranking for wins per season."""
        if df is None or df.empty:
            return df
        df['wins'] = pd.to_numeric(df['wins'], errors='coerce')
        df['losses'] = pd.to_numeric(df['losses'], errors='coerce')
        df['Wins_Rank'] = df.groupby('season_year')['wins'].rank(method='min', ascending=False).astype('Int64')
        return df


class PlayerPageParser:
    """Parse local HTML files of player pages to extract detailed info."""

    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.data = {}

    def _get_text(self, tag, default=''):
        return tag.get_text(strip=True) if tag else default

    def parse(self) -> Dict:
        name_tag = self.soup.find('h1')
        self.data['full_name'] = self._get_text(name_tag)

        info_div = self.soup.find('div', id='info')
        if not info_div:
            return self.data

        info_text = info_div.get_text(separator='\n')

        patterns = {
            'position': r'Position:\s*(.*?)(?:\s*▪|$|\n)',
            'shoots': r'Shoots:\s*(.*?)(?:\s*▪|$|\n)',
            'college': r'College:\s*(.*?)(?:\n|$)',
            'high_school': r'High School:\s*(.*?)(?:\n|$)',
            'draft': r'Draft:\s*(.*?)(?:\n|$)',
            'current_team': r'Current Team:\s*(.*?)(?:\n|$)',
            'pronunciation': r'Pronunciation:\s*(.*?)(?:\n|$)',
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, info_text, re.IGNORECASE)
            self.data[key] = match.group(1).strip() if match else ''
            if self.data[key]:
                self.data[key] = re.sub(r'\s+', ' ', self.data[key])

        nickname_match = re.search(r'\(([^)]+)\)', info_text)
        self.data['nickname'] = nickname_match.group(1) if nickname_match else ''
        if not self.data['nickname']:
            nick_tag = self.soup.find('span', class_='nickname')
            if nick_tag:
                self.data['nickname'] = self._get_text(nick_tag)
        if not self.data['nickname'] and name_tag:
            match = re.search(r'\(([^)]+)\)', name_tag.get_text())
            if match:
                self.data['nickname'] = match.group(1)

        birth_span = self.soup.find('span', id='necro-birth')
        if birth_span and birth_span.get('data-birth'):
            birth_date_str = birth_span.get('data-birth')
            try:
                birth_dt = datetime.strptime(birth_date_str, '%Y-%m-%d')
                self.data['birth_year'] = birth_dt.year
                self.data['age'] = datetime.now().year - birth_dt.year
                born_match = re.search(r'Born:\s*(.*?)(?:\s*\(|$|\n)', info_text, re.IGNORECASE)
                self.data['born'] = born_match.group(1).strip() if born_match else self._get_text(birth_span)
                if self.data['born'] and not re.search(r'\d{4}', self.data['born']):
                    self.data['born'] = f"{self.data['born']}, {birth_dt.year}"
            except ValueError:
                self._parse_born_from_info(info_text)
        else:
            self._parse_born_from_info(info_text)

        self.data['nationality'] = self._extract_nationality(self.data.get('born', ''))
        self._parse_height_weight(info_div)

        meta_div = self.soup.find('div', id='meta')
        if meta_div:
            img = meta_div.find('img')
            self.data['photo_url'] = img.get('src') if img and img.get('src') else ''
        else:
            self.data['photo_url'] = ''

        for k, v in self.data.items():
            if isinstance(v, str):
                self.data[k] = v.strip()

        return self.data

    def _parse_born_from_info(self, info_text):
        match = re.search(r'Born:\s*(.*?)(?:\s*\(|$|\n)', info_text, re.IGNORECASE)
        if match:
            born_raw = match.group(1).strip()
            self.data['born'] = born_raw
            year_match = re.search(r'\b(\d{4})\b', born_raw)
            self.data['birth_year'] = int(year_match.group(1)) if year_match else ''
            self.data['age'] = datetime.now().year - int(year_match.group(1)) if year_match else ''
        else:
            self.data['born'] = ''
            self.data['birth_year'] = ''
            self.data['age'] = ''

    def _extract_nationality(self, born_text):
        if not born_text:
            return ''
        parts = [p.strip() for p in born_text.split(',')]
        if len(parts) >= 2:
            last = parts[-1]
            if re.match(r'^[a-z]{2}$', last):
                return last.upper()
            return last
        return ''

    def _parse_height_weight(self, info_div):
        p_tags = info_div.find_all('p')
        for p in p_tags:
            spans = p.find_all('span')
            if len(spans) >= 2:
                height_span = spans[0].get_text(strip=True) if len(spans) > 0 else ''
                weight_span = spans[1].get_text(strip=True) if len(spans) > 1 else ''
                metric_span = spans[2].get_text(strip=True) if len(spans) > 2 else ''

                self.data['height_display'] = height_span
                self.data['weight_display'] = weight_span
                self.data['height_inches'] = self._parse_height_inches(height_span)
                self.data['height_cm'] = self._parse_height_cm(height_span, metric_span)
                self.data['weight_lbs'] = self._parse_weight_lbs(weight_span)
                self.data['weight_kg'] = self._parse_weight_kg(weight_span, metric_span)
                self.data['height'] = height_span
                self.data['weight'] = weight_span
                break

        if 'height_display' not in self.data:
            self._fallback_parse_height_weight(info_div.get_text(separator='\n'))

    def _fallback_parse_height_weight(self, info_text):
        match = re.search(r'(\d+-\d+)\s*,\s*(\d+)\s*(?:lbs?|lb|pounds?)\s*\((\d+)\s*cm,\s*(\d+)\s*kg\)', info_text, re.IGNORECASE)
        if match:
            self.data['height_display'] = match.group(1)
            self.data['weight_display'] = match.group(2) + 'lb'
            self.data['height_inches'] = self._parse_height_inches(match.group(1))
            self.data['height_cm'] = int(match.group(3))
            self.data['weight_lbs'] = int(match.group(2))
            self.data['weight_kg'] = int(match.group(4))
            self.data['height'] = match.group(1)
            self.data['weight'] = match.group(2) + 'lb'
        else:
            h_match = re.search(r'(\d+)-(\d+)', info_text)
            if h_match:
                self.data['height_display'] = f"{h_match.group(1)}-{h_match.group(2)}"
                self.data['height_inches'] = int(h_match.group(1))*12 + int(h_match.group(2))
                self.data['height_cm'] = round(self.data['height_inches'] * 2.54)
            w_match = re.search(r'(\d+)\s*(?:lbs?|lb|pounds?)', info_text, re.IGNORECASE)
            if w_match:
                self.data['weight_display'] = w_match.group(1) + 'lb'
                self.data['weight_lbs'] = int(w_match.group(1))
                self.data['weight_kg'] = round(int(w_match.group(1)) / 2.20462)

    @staticmethod
    def _parse_height_inches(height_str):
        if not height_str:
            return ''
        match = re.search(r'(\d+)-(\d+)', height_str)
        if match:
            return int(match.group(1))*12 + int(match.group(2))
        if height_str.isdigit():
            return int(height_str)
        return ''

    @staticmethod
    def _parse_height_cm(height_span, metric_span):
        if metric_span:
            cm_match = re.search(r'(\d+)\s*cm', metric_span, re.IGNORECASE)
            if cm_match:
                return int(cm_match.group(1))
        inches = PlayerPageParser._parse_height_inches(height_span)
        if inches:
            return round(inches * 2.54)
        return ''

    @staticmethod
    def _parse_weight_lbs(weight_span):
        if not weight_span:
            return ''
        match = re.search(r'(\d+)', weight_span)
        if match:
            return int(match.group(1))
        return ''

    @staticmethod
    def _parse_weight_kg(weight_span, metric_span):
        if metric_span:
            kg_match = re.search(r'(\d+)\s*kg', metric_span, re.IGNORECASE)
            if kg_match:
                return int(kg_match.group(1))
        lbs = PlayerPageParser._parse_weight_lbs(weight_span)
        if lbs:
            return round(lbs / 2.20462)
        return ''
