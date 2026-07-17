import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def get_all_active_players_seasons_teams():
    headers = {'User-Agent': 'Mozilla/5.0 (Linux NT 10.0; Win64; x64) AppleWebKit/537.36'}
    all_data = []
    total_active_players = 0

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
                        selected_columns = []
                        if 'Season' in seasons_df.columns:
                            selected_columns.append('Season')
                        elif 'season' in seasons_df.columns:
                            selected_columns.append('season')
                        
                        if 'Team' in seasons_df.columns:
                            selected_columns.append('Team')
                        elif 'team' in seasons_df.columns:
                            selected_columns.append('team')
                        elif 'Tm' in seasons_df.columns:
                            selected_columns.append('Tm')
                        elif 'tm' in seasons_df.columns:
                            selected_columns.append('tm')

                        if len(selected_columns) >= 2:
                            temp_df = seasons_df[selected_columns].copy()
                            temp_df['PlayerName'] = player_name
                            temp_df['PlayerURL'] = player_url
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
    get_all_active_players_seasons_teams()
