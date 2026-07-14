import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_active_players():
    base_url = 'https://www.basketball-reference.com/players/'
    letters = 'abcdefghijklmnopqrstuvwxyz'
    all_players = []
    
    for letter in letters:
        url = f'{base_url}{letter}/'
        print(f'Lookin in  {url} ...')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            table = soup.find('table')
            if not table:
                print(f'No table found for letter {letter}')
                continue
            
            rows = table.find_all('tr')
            
            for row in rows:
                player_link = row.find('a')
                if not player_link:
                    continue
                
                is_active = False
                if player_link.parent and player_link.parent.name == 'strong':
                    is_active = True
                elif player_link.find_parent('strong'):
                    is_active = True
                elif row.find('strong'):
                    is_active = True
                
                if not is_active:
                    continue
                
                cols = row.find_all(['td', 'th'])
                if len(cols) < 7:
                    continue
                
                player_name = player_link.get_text(strip=True)
                player_url = 'https://www.basketball-reference.com' + player_link.get('href', '')
                
                player_id = player_url.split('/')[-1].replace('.html', '')
                
                from_year = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                to_year = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                position = cols[3].get_text(strip=True) if len(cols) > 3 else ''
                height = cols[4].get_text(strip=True) if len(cols) > 4 else ''
                weight = cols[5].get_text(strip=True) if len(cols) > 5 else ''
                birth_date = cols[6].get_text(strip=True) if len(cols) > 6 else ''
                college = cols[7].get_text(strip=True) if len(cols) > 7 else ''
                
                all_players.append({
                    'PlayerID': player_id,
                    'PlayerName': player_name,
                    'PlayerURL': player_url,
                    'From': from_year,
                    'To': to_year,
                    'Pos': position,
                    'Ht': height,
                    'Wt': weight,
                    'BirthDate': birth_date,
                    'College': college
                })
            
            print(f'Found {len([p for p in all_players if p["PlayerID"].startswith(letter)])} active players for letter {letter}')
            time.sleep(1)
            
        except Exception as e:
            print(f'Error fetching {url}: {e}')
            continue
    
    return all_players

def main():
    print('Starting to fetch active NBA players...')
    players = get_active_players()
    
    if players:
        df = pd.DataFrame(players)
        df.to_csv('nba_active_players.csv', index=False, encoding='utf-8-sig')
        print(f'Successfully saved {len(players)} active players to nba_active_players.csv')
    else:
        print('No active players found.')

if __name__ == '__main__':
    main()
