import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_team_mapping():
    url = 'https://www.basketball-reference.com/teams/'
    headers = {'User-Agent': 'Mozilla/5.0 (Linux NT 10.0; Win64; x64) AppleWebKit/537.36'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    mapping = {}
    table = None
    for h in soup.find_all(['h2', 'h3']):
        if 'Active Franchises' in h.get_text():
            table = h.find_next('table')
            break
    
    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])
            if len(cols) >= 2:
                link = cols[0].find('a') if cols[0].find('a') else None
                if link:
                    full_name = link.get_text(strip=True)
                    href = link.get('href', '')
                    match = re.search(r'/teams/([A-Z]{2,3})/', href)
                    if match:
                        abbr = match.group(1)
                        mapping[abbr] = full_name
                    else:
                        text = cols[0].get_text(strip=True)
                        abbr_match = re.search(r'\(([A-Z]{2,3})\)', text)
                        if abbr_match:
                            abbr = abbr_match.group(1)
                            mapping[abbr] = full_name
    
    extra_teams = {
        'BRK': 'Brooklyn Nets',
        'NJN': 'New Jersey Nets',
        'NOK': 'New Orleans Hornets',
        'NOP': 'New Orleans Pelicans',
        'CHA': 'Charlotte Hornets',
        'CHH': 'Charlotte Hornets',
        'VAN': 'Vancouver Grizzlies',
        'SEA': 'Seattle SuperSonics',
        'OKC': 'Oklahoma City Thunder',
        'WSB': 'Washington Bullets',
        'WAS': 'Washington Wizards',
        'PHO': 'Phoenix Suns',
        'PHX': 'Phoenix Suns',
        'SAS': 'San Antonio Spurs',
        'TOR': 'Toronto Raptors',
        'MIA': 'Miami Heat',
        'ORL': 'Orlando Magic',
        'ATL': 'Atlanta Hawks',
        'BOS': 'Boston Celtics',
        'CHI': 'Chicago Bulls',
        'CLE': 'Cleveland Cavaliers',
        'DAL': 'Dallas Mavericks',
        'DEN': 'Denver Nuggets',
        'DET': 'Detroit Pistons',
        'GSW': 'Golden State Warriors',
        'HOU': 'Houston Rockets',
        'IND': 'Indiana Pacers',
        'LAC': 'Los Angeles Clippers',
        'LAL': 'Los Angeles Lakers',
        'MEM': 'Memphis Grizzlies',
        'MIL': 'Milwaukee Bucks',
        'MIN': 'Minnesota Timberwolves',
        'NYK': 'New York Knicks',
        'PHI': 'Philadelphia 76ers',
        'POR': 'Portland Trail Blazers',
        'SAC': 'Sacramento Kings',
        'UTA': 'Utah Jazz',
        'UTA': 'Utah Jazz',
    }
    mapping.update(extra_teams)
    
    return mapping

def get_all_active_players_seasons_full_team():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    all_data = []
    total_active_players = 0
    
    print('Fetching team name mapping...')
    team_mapping = get_team_mapping()
    print(f'Loaded mapping for {len(team_mapping)} teams.')
    
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        letter_url = f'https://www.basketball-reference.com/players/{letter}/'
        print(f'Checking letter: {letter.upper()} ...')

        try:
            response = requests.get(letter_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            active_players = []
            for strong_tag in soup.find_all('strong'):
                link = strong_tag.find('a')
                if link and link.get('href', '').startswith('/players/') and link.get('href', '').endswith('.html'):
                    player_name = link.get_text(strip=True)
                    player_url = 'https://www.basketball-reference.com' + link.get('href')
                    active_players.append((player_name, player_url))

            print(f'  Found {len(active_players)} active players for letter {letter.upper()}')
            total_active_players += len(active_players)

            for idx, (player_name, player_url) in enumerate(active_players, 1):
                print(f'    ({idx}/{len(active_players)}) Fetching {player_name} ...')
                try:
                    resp = requests.get(player_url, headers=headers)
                    tables = pd.read_html(player_url)

                    seasons_df = None
                    for df in tables:
                        cols = [c.lower() for c in df.columns]
                        if 'season' in cols or 'lg' in cols:
                            seasons_df = df
                            break

                    if seasons_df is not None:
                        season_col = None
                        team_col = None
                        for col in seasons_df.columns:
                            if col.lower() == 'season':
                                season_col = col
                            elif col.lower() in ['team', 'tm']:
                                team_col = col
                        
                        if season_col and team_col:
                            temp_df = seasons_df[[season_col, team_col]].copy()
                            temp_df['PlayerName'] = player_name
                            temp_df['PlayerURL'] = player_url
                            
                            temp_df['TeamFullName'] = temp_df[team_col].map(team_mapping).fillna(temp_df[team_col])
                            temp_df = temp_df.rename(columns={season_col: 'Season', team_col: 'TeamAbbr'})
                            temp_df = temp_df.drop(columns=['TeamAbbr'])
                            temp_df = temp_df.rename(columns={'TeamFullName': 'Team'})
                            
                            all_data.append(temp_df)
                        else:
                            print(f'      Required columns not found for {player_name}')
                    else:
                        print(f'      No season table found for {player_name}')

                except Exception as e:
                    print(f'      Error fetching {player_name}: {e}')

                time.sleep(1)

            time.sleep(1)

        except Exception as e:
            print(f'  Error fetching letter page {letter}: {e}')
            continue

    print(f'Total active players found across all letters: {total_active_players}')

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.to_csv('nba_active_players_seasons_teams.csv', index=False, encoding='utf-8-sig')
        print('Successfully saved data to nba_active_players_seasons_teams.csv')
    else:
        print('No data retrieved.')

if __name__ == '__main__':
    get_all_active_players_seasons_full_team()
