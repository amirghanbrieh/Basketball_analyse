import os
import sys
import re
import time
from datetime import datetime

import pandas as pd
from colorama import init, Fore, Back, Style

from utils import (
    SeasonScraper,
    ActivePlayersScraper,
    TeamsSummaryScraper,
    TeamSeasonScraper,
    PlayerStatsScraper,
    PlayerPageParser
)

# Init colorama
init(autoreset=True)


def ensure_dir(directory: str):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"{Fore.GREEN}Created directory: {directory}")


def print_step_header(step_num: int, title: str):
    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}{Style.BRIGHT}STEP {step_num}: {title}")
    print("=" * 60)


def run_season_scraper(start_year: int, end_year: int, output_dir: str):
    print_step_header(1, "Scraping season info (Champion, MVP, ...)")
    scraper = SeasonScraper(delay=2)
    results = scraper.scrape_range(start_year, end_year)
    if results:
        df = pd.DataFrame(results)
        outfile = os.path.join(output_dir, 'seasons.csv')
        df.to_csv(outfile, index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Season info saved to {outfile}")
    else:
        print(f"{Fore.RED}No season data retrieved.")


def run_active_players_scraper(output_dir: str):
    print_step_header(2, "Scraping active players list")
    scraper = ActivePlayersScraper(delay=1.5)
    players = scraper.scrape()
    if players:
        df = pd.DataFrame(players)
        outfile = os.path.join(output_dir, 'nba_active_players.csv')
        df.to_csv(outfile, index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Active players saved to {outfile}")
    else:
        print(f"{Fore.RED}No active players found.")


def run_teams_summary_scraper(output_dir: str):
    print_step_header(3, "Scraping teams summary")
    scraper = TeamsSummaryScraper(delay=1)
    summary_df, team_links = scraper.scrape()
    if not summary_df.empty:
        outfile = os.path.join(output_dir, 'nba_teams_summary.csv')
        summary_df.to_csv(outfile, index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Teams summary saved to {outfile}")
        # Save links for possible later use
        links_df = pd.DataFrame({'TeamURL': team_links})
        links_df.to_csv(os.path.join(output_dir, 'nba_team_links.csv'), index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Team links saved to {os.path.join(output_dir, 'nba_team_links.csv')}")
    else:
        print(f"{Fore.RED}No team summary data.")


def run_team_season_scraper(start_year: int, end_year: int, output_dir: str):
    print_step_header(4, "Scraping detailed team-season data")
    scraper = TeamSeasonScraper(delay=2)
    results = scraper.scrape_range(start_year, end_year)
    if results:
        df = pd.DataFrame(results)
        outfile = os.path.join(output_dir, 'NBA_2018_2026.csv')
        df.to_csv(outfile, index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Team-season data saved to {outfile}")
    else:
        print(f"{Fore.RED}No team-season data.")


def run_player_stats_scraper(start_year: int, end_year: int, output_dir: str):
    print_step_header(5, "player and team stats with rankings")
    scraper = PlayerStatsScraper(delay=1.5)

    all_teams = []
    all_players = []

    for year in range(start_year, end_year + 1):
        print(f"\n{Fore.YELLOW}Processing season {year-1}-{year}")
        teams = scraper.scrape_teams_season(year)
        if teams:
            all_teams.extend(teams)
            print(f"   {Fore.GREEN}Found {len(teams)} teams")
        players_df = scraper.scrape_players_season(year)
        if players_df is not None and not players_df.empty:
            all_players.append(players_df)
            print(f"   {Fore.GREEN}Found {len(players_df)} players")
        time.sleep(2)

    if all_teams:
        teams_df = pd.DataFrame(all_teams)
        teams_df = scraper.add_team_rankings(teams_df)
        outfile_teams = os.path.join(output_dir, 'nba_teams_2018_2026.csv')
        teams_df.to_csv(outfile_teams, index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Team stats saved to {outfile_teams}")

    if all_players:
        players_df = pd.concat(all_players, ignore_index=True)
        players_df = scraper.add_player_rankings(players_df)
        outfile_players = os.path.join(output_dir, 'nba_players_2018_2026.csv')
        players_df.to_csv(outfile_players, index=False, encoding='utf-8-sig')
        print(f"{Fore.GREEN}Player stats saved to {outfile_players}")


def run_player_page_parser(input_dir: str, output_dir: str):
    print_step_header(6, "Parsing local player HTML files (Optional)")

    if not os.path.exists(input_dir):
        print(f"{Fore.YELLOW}Directory {input_dir} not found. Skipping.")
        return

    all_players = []
    html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]
    if not html_files:
        print(f"{Fore.YELLOW}No HTML files found in directory. Skipping.")
        return

    total = len(html_files)
    for idx, filename in enumerate(html_files, 1):
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        parser = PlayerPageParser(html)
        data = parser.parse()
        data['file'] = filename
        all_players.append(data)
        print(f"[{idx}/{total}] Processed {Fore.CYAN}{data.get('full_name', filename)}")

    if all_players:
        fieldnames = ['full_name', 'nickname', 'position', 'shoots', 'born', 'age',
                      'nationality', 'height', 'height_inches', 'weight', 'weight_lbs',
                      'college', 'high_school', 'draft', 'current_team', 'pronunciation',
                      'photo_url', 'file']
        df = pd.DataFrame(all_players)
        # Fill missing age if possible
        for idx, row in df.iterrows():
            if pd.isna(row.get('age')) and row.get('born'):
                birth_str = row.get('born', '')
                if birth_str:
                    year_match = re.search(r'\b(\d{4})\b', birth_str)
                    if year_match:
                        birth_year = int(year_match.group(1))
                        df.at[idx, 'age'] = datetime.now().year - birth_year

        outfile = os.path.join(output_dir, 'players_parsed.csv')
        df.to_csv(outfile, index=False, encoding='utf-8-sig', columns=fieldnames)
        print(f"{Fore.GREEN}Parsed players saved to {outfile}")
    else:
        print(f"{Fore.RED}No player data parsed.")


def main():
    # setting setup
    START_YEAR = 2018
    END_YEAR = 2026
    OUTPUT_DIR = 'data'
    PLAYER_HTML_DIR = 'basketball_pages/gamers'  

    # this is my banner :)))
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}NBA DATA SCRAPER - BASKETBALL REFERENCE")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}Period: {START_YEAR}-{END_YEAR}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*60}")

    ensure_dir(OUTPUT_DIR)

    # Run steps by steps
    run_season_scraper(START_YEAR, END_YEAR, OUTPUT_DIR)
    run_active_players_scraper(OUTPUT_DIR)
    run_teams_summary_scraper(OUTPUT_DIR)
    run_team_season_scraper(START_YEAR, END_YEAR, OUTPUT_DIR)
    run_player_stats_scraper(START_YEAR, END_YEAR, OUTPUT_DIR)

    if os.path.exists(PLAYER_HTML_DIR):
        run_player_page_parser(PLAYER_HTML_DIR, OUTPUT_DIR)
    else:
        print(f"\n{Fore.YELLOW}Optional step skipped: {PLAYER_HTML_DIR} not found.")

    print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.GREEN}{Style.BRIGHT}ALL STEPS COMPLETED.")
    print(f"{Fore.GREEN}{Style.BRIGHT}Outputs saved in '{OUTPUT_DIR}' directory.")
    print(f"{Fore.GREEN}{Style.BRIGHT}{'='*60}")


if __name__ == "__main__":
    main()
