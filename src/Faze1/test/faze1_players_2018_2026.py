import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

class NBAScraper:
    def __init__(self, start_year=2018, end_year=2026):
        self.start_year = start_year
        self.end_year = end_year
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.teams_data = None
        self.players_data = None

    def _get_team_details(self, team_url):
        if not team_url:
            return {'coach': '', 'arena': '', 'attendance': '', 'top_players': ''}
        if not team_url.startswith('http'):
            team_url = f"https://www.basketball-reference.com{team_url}"
        try:
            resp = requests.get(team_url, headers=self.headers, timeout=10)
            resp.raise_for_status()
        except Exception:
            return {'coach': '', 'arena': '', 'attendance': '', 'top_players': ''}
        soup = BeautifulSoup(resp.text, 'html.parser')
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

    def _get_season_teams(self, year):
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        tables = []
        table_e = soup.find('table', {'id': 'confs_standings_E'})
        table_w = soup.find('table', {'id': 'confs_standings_W'})
        if table_e:
            tables.append(table_e)
        if table_w:
            tables.append(table_w)
        if not tables:
            standings_table = soup.find('div', id='all_standings')
            if standings_table:
                standings_table = standings_table.find('table')
            if not standings_table:
                standings_table = soup.find('table', {'class': 'stats_table'})
            if standings_table:
                tables.append(standings_table)
        if not tables:
            return []
        teams = []
        for table in tables:
            tbody = table.find('tbody')
            if not tbody:
                continue
            rows = tbody.find_all('tr')
            for row in rows:
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
                time.sleep(0.3)
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
        return teams

    def _get_season_totals(self, year):
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}_totals.html"
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'id': 'totals_stats'})
        if not table:
            return None
        thead = table.find('thead')
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

    def _add_player_rankings(self, df):
        if df is None or df.empty:
            return df
        stat_cols = ['PTS', 'TRB', 'AST', 'STL', 'BLK', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB', 'TOV', 'PF', 'MP']
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
            df['PTS_Norm'] = df.groupby('Season_Year')['PTS'].transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0)
            df['TRB_Norm'] = df.groupby('Season_Year')['TRB'].transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0)
            df['AST_Norm'] = df.groupby('Season_Year')['AST'].transform(lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0)
            df['Combined_Score'] = df['PTS_Norm'] * 0.4 + df['TRB_Norm'] * 0.3 + df['AST_Norm'] * 0.3
            df['Overall_Rank'] = df.groupby('Season_Year')['Combined_Score'].rank(method='min', ascending=False).astype('Int64')
        return df

    def _add_team_rankings(self, df):
        if df is None or df.empty:
            return df
        df['wins'] = pd.to_numeric(df['wins'], errors='coerce')
        df['losses'] = pd.to_numeric(df['losses'], errors='coerce')
        df['Wins_Rank'] = df.groupby('season_year')['wins'].rank(method='min', ascending=False).astype('Int64')
        return df

    def scrape_all(self):
        print(f"Scraping NBA data from {self.start_year} to {self.end_year}...")
        all_teams = []
        all_players = []
        for year in range(self.start_year, self.end_year + 1):
            print(f"\nProcessing season {year-1}-{str(year)[-2:]}...")
            teams = self._get_season_teams(year)
            if teams:
                all_teams.extend(teams)
                print(f"  Found {len(teams)} teams")
            players_df = self._get_season_totals(year)
            if players_df is not None:
                all_players.append(players_df)
                print(f"  Found {len(players_df)} players")
            time.sleep(2)
        self.teams_data = pd.DataFrame(all_teams) if all_teams else None
        self.players_data = pd.concat(all_players, ignore_index=True) if all_players else None
        if self.teams_data is not None:
            self.teams_data = self._add_team_rankings(self.teams_data)
        if self.players_data is not None:
            self.players_data = self._add_player_rankings(self.players_data)
        return self.teams_data, self.players_data

    def save_data(self, teams_file='nba_teams_2018_2026.csv', players_file='nba_players_2018_2026.csv'):
        if self.teams_data is not None and not self.teams_data.empty:
            self.teams_data.to_csv(teams_file, index=False, encoding='utf-8-sig')
            print(f"Team data saved to '{teams_file}'")
        else:
            print("No team data to save.")
        if self.players_data is not None and not self.players_data.empty:
            self.players_data.to_csv(players_file, index=False, encoding='utf-8-sig')
            print(f"Player data saved to '{players_file}'")
        else:
            print("No player data to save.")

    def get_season_summary(self):
        if self.teams_data is None or self.teams_data.empty:
            print("No data available. Run scrape_all() first.")
            return
        print("\n" + "="*60)
        print("NBA SEASON SUMMARY (2018-2026)")
        print("="*60)
        for year in range(self.start_year, self.end_year + 1):
            season_label = f"{year-1}-{str(year)[-2:]}"
            season_teams = self.teams_data[self.teams_data['season_year'] == year]
            if not season_teams.empty:
                best_team = season_teams.loc[season_teams['wins'].idxmax()]
                print(f"\n{season_label}:")
                print(f"  Best Team: {best_team['team']} ({best_team['wins']}-{best_team['losses']})")
            if self.players_data is not None and not self.players_data.empty:
                season_players = self.players_data[self.players_data['Season_Year'] == year]
                if not season_players.empty and 'Overall_Rank' in season_players.columns:
                    top_player = season_players[season_players['Overall_Rank'] == 1]
                    if not top_player.empty:
                        p = top_player.iloc[0]
                        pts = p.get('PTS', 'N/A')
                        trb = p.get('TRB', 'N/A')
                        ast = p.get('AST', 'N/A')
                        print(f"  Top Player: {p['Player']} ({pts} PTS, {trb} REB, {ast} AST)")

if __name__ == "__main__":
    start_time = datetime.now()
    scraper = NBAScraper(start_year=2018, end_year=2026)
    scraper.scrape_all()
    scraper.save_data()
    scraper.get_season_summary()
    print(f"\nExecution time: {(datetime.now() - start_time).total_seconds():.2f} seconds")
    print("Done.")
