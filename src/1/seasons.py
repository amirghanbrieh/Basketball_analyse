import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_season(season_end_year):
    url = f'https://www.basketball-reference.com/leagues/NBA_{season_end_year}.html'
    print(f"Processing: {url}")
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching page for {season_end_year}: {e}")
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    
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

    label_map = {
        "League Champion": "Champion",
        "Most Valuable Player": "MVP",
        "Rookie of the Year": "ROY",
        "PPG Leader": "PPG_Leader",
        "RPG Leader": "RPG_Leader",
        "APG Leader": "APG_Leader",
        "WS Leader": "WS_Leader"
    }

    for p in soup.find_all('p'):
        strong = p.find('strong')
        if strong:
            strong_text = strong.get_text(strip=True).replace(':', '')
            if strong_text in label_map:
                full_text = p.get_text(separator=' ', strip=True)
                if ':' in full_text:
                    value = full_text.split(':', 1)[1].strip()
                    data[label_map[strong_text]] = value

    return data

if __name__ == "__main__":
    seasons = list(range(2018, 2027))

    all_data = []
    for year in seasons:
        result = scrape_season(year)
        if result:
            all_data.append(result)
        time.sleep(5)

    df = pd.DataFrame(all_data)
    print("\n" + "="*80)
    print("Extracted Results:")
    print("="*80)
    print(df.to_string(index=False))

    df.to_csv('seasons_2018_2026.csv', index=False, encoding='utf-8-sig')
    print("\nCSV file 'seasons_2018_2026.csv' has been saved.")
