
from .cleaner import *

def club_dataframe():

    club_read_data = Read_Data("Data/clubs.xlsx")
    df_club = club_read_data.read_excel()
    
    club_clean = Club_Cleaner(df_club)
    df_club = club_clean.keep_longest_active_club()
    df_club = club_clean.select_rename()
    df_club = club_clean.set_primary_key()
    return df_club


def player_dataframe():

    player_read_data = Read_Data("Data/players.csv")
    df_player = player_read_data.read_csv()

    player_clean = Player_Cleaner(df_player)
    df_player = player_clean.select_rename()
    df_player = player_clean.update_player_columns("Data/players_complementrycsv.xlsx")
    df_player = player_clean.set_primary_key()
    df_player = df_player.rename(columns={
        'From': 'from_year',
        'To': 'to_year',})
   
    return df_player


def nickname_dataframe(player_df):

    player_clean = Player_Cleaner(player_df)
    nickname_df = player_clean.separete_of_column("nickname","id" ,"player_id")
    nickname_clean = Data_Cleaner(nickname_df)
    nickname_df = nickname_clean.remove_null_rows("name")
    nickname_df = nickname_clean.set_primary_key()

    return nickname_df, player_clean._dataframe


def season_dataframe():

    season_read_data = Read_Data("Data/seasons.xlsx")
    df_season = season_read_data.read_excel()

    season_clean = Season_Cleaner(df_season)
    df_season = season_clean.select_rename()
    df_season = season_clean.set_primary_key()
    
    return df_season


def season_club_dataframe(club_df,season_df):

    season_club_read_data = Read_Data("Data/seasons_club.csv.xlsx")
    df_season_club = season_club_read_data.read_excel()

    season_club_clean = Season_Club_Cleaner(df_season_club)
    df_season_club = season_club_clean.select_rename()
    df_season_club = season_club_clean.extract_rank()
    df_season_club = season_club_clean.remove_trailing_asterisk()
    df_season_club = season_club_clean.map_column_to_id("club_id",club_df,"name","id")
    df_season_club = season_club_clean.fix_season_years_format()
    df_season_club = season_club_clean.map_column_to_id("season_id",season_df,"season_years","id")
    df_season_club = season_club_clean.remove_null_rows("season_id")
    df_season_club = season_club_clean.remove_null_rows("club_id")
    df_season_club = season_club_clean.set_primary_key()

    return df_season_club


def season_player_dataframe(player_df,season_df):

    season_player_read_data = Read_Data("Data/season_player.xlsx")
    df_season_player = season_player_read_data.read_excel()
    
    season_player_clean = Season_Player_Cleaner(df_season_player)
    df_season_player = season_player_clean.select_rename()
    
    df_season_player = season_player_clean.map_column_to_id("season_id",season_df,"season_years","id")
    df_season_player = season_player_clean.map_column_to_id("player_id",player_df,"fullname","id")
    df_season_player = season_player_clean.remove_null_rows("season_id")
    df_season_player = season_player_clean.remove_null_rows("player_id")

    df_season_player = season_player_clean.set_primary_key()

    return df_season_player


def awards_dataframe(season_player_df):

    season_player_clean = Season_Player_Cleaner(season_player_df)
    awards_dataframe = season_player_clean.separete_of_column("Awards","id" ,"season_player_id")

    award_clean = Data_Cleaner(awards_dataframe)
    awards_df = award_clean.remove_null_rows("name")
    awards_df = award_clean.set_primary_key()
    return awards_df, season_player_clean._dataframe


def high_school_dataframe(player_df):
    player_clean = Player_Cleaner(player_df)
    high_school_df, player_df = player_clean.extract_highschool_and_map()

    return high_school_df, player_df
     

def college_dataframe(player_df):
    player_clean = Player_Cleaner(player_df)
    college_df, player_df = player_clean.extract_and_map_lookup("college","college_id")
    
    return college_df, player_df


def position_dataframe(player_df):
    player_clean = Player_Cleaner(player_df)
    position_df, position_player_df,player_df = player_clean.extract_positions_many_to_many("position","id","player_id","position_id")
    
    return position_df, position_player_df,player_df


def coach_dataframe(club_season_df):
    club_season_clean = Season_Club_Cleaner(club_season_df)
    coach_df, coach_season_club_df,club_season_df = club_season_clean.extract_coaches_many_to_many()

    return  coach_df, coach_season_club_df,club_season_df


def player_season_club(player_df,season_df,club_df):
    player_season_club_read_data = Read_Data("Data/active_players_seasons_teams.csv.xlsx")
    df_player_season_club = player_season_club_read_data.read_excel()
    
    player_season_club_clean = Season_Player_CLub(df_player_season_club)
    df_player_season_club = player_season_club_clean.select_rename()
    df_player_season_club = player_season_club_clean.clean_season_column()
    df_player_season_club = player_season_club_clean.fix_season_years_format()
    df_player_season_club = player_season_club_clean.map_column_to_id("player_id",player_df,"fullname","id")
    df_player_season_club = player_season_club_clean.map_column_to_id("season_id",season_df,"season_years","id")
    df_player_season_club = player_season_club_clean.map_column_to_id("club_id",club_df,"name","id")
    df_player_season_club = player_season_club_clean.remove_null_rows("club_id")
    df_player_season_club = player_season_club_clean.remove_null_rows("season_id")
    df_player_season_club = player_season_club_clean.remove_null_rows("player_id")
    df_player_season_club = player_season_club_clean.set_primary_key()
    return df_player_season_club


   

    


def clean_all_data():
    df_club_clean = club_dataframe()
    df_player_clean = player_dataframe()
    df_nickname_clean, df_player_clean  = nickname_dataframe(df_player_clean)
    df_season_clean = season_dataframe()
    df_season_club_clean = season_club_dataframe(df_club_clean, df_season_clean)
    df_season_player_clean = season_player_dataframe(df_player_clean,df_season_clean)
    df_awards_clean, df_season_player_clean = awards_dataframe(df_season_player_clean)
    df_high_school_clean ,df_player_clean = high_school_dataframe(df_player_clean)
    df_college_clean, df_player_clean = college_dataframe(df_player_clean)
    df_position_clean, df_position_player_clean, df_player_clean = position_dataframe(df_player_clean)
    df_coach_clean, df_coach_season_club_clean, df_season_club_clean = coach_dataframe(df_season_club_clean)
    df_player_season_club_clean = player_season_club(df_player_clean,df_season_clean,df_club_clean)

    cleaned_dfs = {
        "clubs": df_club_clean,
        "players": df_player_clean,
        "nicknames": df_nickname_clean,
        "seasons": df_season_clean,
        "season_clubs": df_season_club_clean,
        "season_players": df_season_player_clean,
        "awards": df_awards_clean,
        "high_schools": df_high_school_clean,
        "colleges": df_college_clean,
        "positions": df_position_clean,
        "player_positions": df_position_player_clean,
        "coaches": df_coach_clean,
        "coach_season_clubs": df_coach_season_club_clean,
        "player_season_club" : df_player_season_club_clean
    }
    
    return cleaned_dfs
