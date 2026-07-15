import os
import re
import time
from io import StringIO  

import pandas as pd
import requests
from bs4 import BeautifulSoup



def get_teams_summary():
    url = 'https://www.basketball-reference.com/teams/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    table = None
    for h in soup.find_all(['h2', 'h3']):
        if 'Active Franchises' in h.get_text():
            table = h.find_next('table')
            break

    if not table:
        dfs = pd.read_html(url, header=0)
        for df in dfs:
            if 'Franchise' in df.columns or 'Lg' in df.columns:
                table_df = df
                break
        else:
            raise Exception('Teams table not found.')
    else:
   
        table_df = pd.read_html(StringIO(str(table)))[0]

    cols = [
        'Franchise',
        'Lg',
        'From',
        'To',
        'Yrs',
        'G',
        'W',
        'L',
        'W/L%',
        'Plyfs',
        'Div',
        'Conf',
        'Champ',
    ]
    table_df.columns = [c.strip() for c in table_df.columns]
    existing_cols = [c for c in cols if c in table_df.columns]
    summary_df = table_df[existing_cols].copy()

    team_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/teams/') and re.match(r'^/teams/[A-Z]{2,3}/$', href):
            full_url = 'https://www.basketball-reference.com' + href
            if full_url not in team_links:
                team_links.append(full_url)

    return summary_df, team_links


def get_team_seasons(team_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    resp = requests.get(team_url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    team_name = soup.find('h1')
    team_name = (
        team_name.get_text(strip=True) if team_name else team_url.split('/')[-2]
    )

    try:
        tables = pd.read_html(team_url, header=0)
    except:
        return None

    seasons_df = None
    for df in tables:
        cols = [c.lower() for c in df.columns]
        if 'season' in cols or 'lg' in cols:
            seasons_df = df
            break

    if seasons_df is None:
        return None

    seasons_df['TeamName'] = team_name
    seasons_df['TeamURL'] = team_url
    return seasons_df


def main():
    print('Fetching team list and summary...')
    summary_df, team_links = get_teams_summary()
    print(f'Found {len(team_links)} teams.')

    summary_df.to_csv(
        'nba_teams_summary.csv', index=False, encoding='utf-8-sig'
    )
    print('Saved nba_teams_summary.csv')

    all_seasons = []
    for i, url in enumerate(team_links, 1):
        print(f'({i}/{len(team_links)}) Fetching data from {url} ...')
        df = get_team_seasons(url)
        if df is not None:
            all_seasons.append(df)

        time.sleep(1)

    if all_seasons:
        combined = pd.concat(all_seasons, ignore_index=True)
        combined.to_csv(
            'nba_teams_seasons.csv', index=False, encoding='utf-8-sig'
        )
        print('Saved nba_teams_seasons.csv')
    else:
        print('No season data retrieved.')


if __name__ == '__main__':
    main()
