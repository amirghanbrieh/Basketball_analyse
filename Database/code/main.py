from Database.connection import *
from Datacleaner.pipeline import clean_all_data

db = DatabaseManager()

db.create_tables()

dfs = clean_all_data()

try:
    db.insert_dataframe(dfs["seasons"], 'season')
    print("The season table was successfully inserted.")
    
    db.insert_dataframe(dfs["clubs"], 'clubs')
    print("The clubs table was successfully inserted.")
    
    db.insert_dataframe(dfs["high_schools"], 'highschool')
    print("The highschool table was successfully inserted.")

    db.insert_dataframe(dfs["colleges"], 'college')
    print("The college table was successfully inserted.")

    db.insert_dataframe(dfs["players"], 'players')
    print("The players table was successfully inserted.")
    
    db.insert_dataframe(dfs["nicknames"], 'nickname')
    print("The nickname table was successfully inserted.")
    
    db.insert_dataframe(dfs["season_clubs"], 'season_club')
    print("The season_club table was successfully inserted.")
    
    db.insert_dataframe(dfs["season_players"], 'season_player')
    print("The season_player table was successfully inserted.")
    
    db.insert_dataframe(dfs["awards"], 'awards')
    print("The awards table was successfully inserted.")

    db.insert_dataframe(dfs["positions"], 'position')
    print("The position table was successfully inserted.")

    db.insert_dataframe(dfs["player_positions"], 'player_position')
    print("The player_position table was successfully inserted.")

    db.insert_dataframe(dfs["coaches"], 'coach')
    print("The coach table was successfully inserted.")

    db.insert_dataframe(dfs["coach_season_clubs"], 'coach_season_club')
    print("The coach_season_club table was successfully inserted.")


    
except Exception as e:
    print(f"Data entry was halted due to an error at one of the stages! Error: {e}")