import pandas as pd

class Read_Data:

    def __init__(self,file_name):
        self.file_name = file_name


    def read_csv(self):
        return pd.read_csv(self.file_name)

    
    def read_excel(self):
        return pd.read_excel(self.file_name)
    

class Data_Cleaner:

    def __init__(self, dataframe):
        self._dataframe = dataframe


    def set_primary_key(self):
        self._dataframe['id'] = range(1, len(self._dataframe) + 1)
        return self._dataframe
    

    def split_and_explode(dataframe, column):
        temp_df = dataframe.copy()
      
        temp_df[column] = temp_df[column].str.replace(r'\s*,\s*and\s+|\s+and\s+', ',', regex=True)
        

        temp_df[column] = temp_df[column].str.replace(r'\s*/\s*', ',', regex=True)

        temp_df[column] = temp_df[column].str.split(',')
        explode_df = temp_df.explode(column)
        explode_df = explode_df.reset_index(drop=True)

        return explode_df
    

    def remove_null_rows(self, column_name):
    
        self._dataframe  =  self._dataframe.dropna(subset=[column_name]).reset_index(drop=True)
        
        return self._dataframe 

    def separete_of_column(self, column, foregin_key_name, new_foregin_key_name):
    

        explode_df = Data_Cleaner.split_and_explode(self._dataframe, column)

        new_table = pd.DataFrame()          
        new_table["name"] = explode_df[column]
        new_table[new_foregin_key_name] = explode_df[foregin_key_name]
        new_table["id"] = new_table.index

        self._dataframe = self._dataframe.drop(column, axis = 1)
        return new_table
    

    def drop_column(self,*columns):
        
        for column in columns:
            self._dataframe = self._dataframe.drop(column,axis = 1)
        return self._dataframe
    

    def rename_columns(self, rename_dict):

        self._dataframe = self._dataframe.rename(columns=rename_dict)
        return self._dataframe


    def select_columns(self, *columns):

        new_table = pd.DataFrame()
        for column in columns:
            new_table[column] = self._dataframe[column]
        
        self._dataframe = new_table
        return self._dataframe
    
    
    def map_column_to_id(self, target_column, reference_df, match_column, id_column):

        mapping_dict = dict(zip(reference_df[match_column], reference_df[id_column]))
        
        self._dataframe[target_column] = self._dataframe[target_column].map(mapping_dict)
        self._dataframe[target_column] = self._dataframe[target_column].astype("Int64") 
        return self._dataframe
    
    
    def extract_and_map_lookup(self, column, new_foreign_key_name):
 
        unique_values = self._dataframe[column].dropna().unique()
        
        lookup_table = pd.DataFrame()
        lookup_table["name"] = unique_values
        lookup_table["id"] = range(1, len(lookup_table) + 1) 


        mapping_dict = dict(zip(lookup_table["name"], lookup_table["id"]))

        self._dataframe[new_foreign_key_name] = self._dataframe[column].map(mapping_dict)

        self._dataframe = self._dataframe.drop(column, axis=1)

     
        return lookup_table, self._dataframe
    

    def extract_positions_many_to_many(self, column, id_column,pivot_first_id,pivot_second_id):
    
      
        exploded_df = Data_Cleaner.split_and_explode(self._dataframe, column)

        unique_positions = exploded_df[column].unique()
        lookup_table = pd.DataFrame()
        lookup_table["name"] = unique_positions
        lookup_table["id"] = range(1, len(lookup_table) + 1) 

    
        position_map = dict(zip(lookup_table["name"], lookup_table["id"]))

      
        bridge_table = pd.DataFrame()
        bridge_table[pivot_first_id] = exploded_df[id_column]
        bridge_table[pivot_second_id] = exploded_df[column].map(position_map)
        
        bridge_table = bridge_table.drop_duplicates().reset_index(drop=True)
        bridge_table["id"] = range(1, len(bridge_table) + 1) 

        self._dataframe = self._dataframe.drop(column, axis=1)

        return lookup_table, bridge_table,self._dataframe


class Club_Cleaner(Data_Cleaner):
    def __init__(self, dataframe):
        super().__init__(dataframe)


    def select_rename(self):
        super().set_primary_key()
        super().drop_column(*["Div","W/L%","Plyfs"])
        column_rename = {
            "Franchise": "name",     
            "Lg": "league",           
            "From": "foundation",   
            "To": "to",                
            "Yrs": "year",             
            "G": "game",               
            "W": "win",                 
            "L": "loss",                
            "Conf": "conf",           
            "Champ": "champ"          
        }
        super().rename_columns(column_rename)
        return self._dataframe
    import pandas as pd
    
    def keep_longest_active_club(self):
        
        df_sorted = self._dataframe.sort_values(by=['Franchise', 'Yrs'], ascending=[True, False])
        
        self._dataframe = df_sorted.drop_duplicates(subset=['Franchise'], keep='first')
    
        return self._dataframe.sort_index()


class Player_Cleaner(Data_Cleaner):
    def __init__(self, dataframe):
        super().__init__(dataframe)


    def select_rename(self):
        select_column = ["full_name","nickname", "position","shoots","nationality","height_inches","weight_lbs","college","high_school","draft","photo_url"]
        super().select_columns(select_column)
        column_rename = {
            "full_name": "fullname",
            "position": "position",
            "shoots": "shoots",
            "nationality": "born_year",
            "height_inches": "height",
            "weight_lbs": "weight",
            "college": "college",
            "high_school": "highschool",
            "draft": "club_id",
            "photo_url": "image_url"}
        super().rename_columns(column_rename)
        
        return self._dataframe

    def update_player_columns(self, csv_path):
        new_data = pd.read_excel(csv_path)

        new_data = new_data[['PlayerName', 'From', 'To']]

        merged_df = pd.merge(
            self._dataframe, 
            new_data, 
            left_on='fullname',   
            right_on='PlayerName',
            how='left'            
        )
    
        merged_df['is_active'] = merged_df['PlayerName'].notna()
        
        merged_df = merged_df.drop(columns=['PlayerName'])
        self._dataframe = merged_df
        return  self._dataframe 

    def extract_highschool_and_map(self, column="highschool", new_foreign_key_name="highschool_id"):
    
        df_temp = self._dataframe[[column]].dropna().copy()
        
        df_temp[column] = df_temp[column].astype(str).str.rstrip(', ')


        split_data = df_temp[column].str.extract(r'^(?P<school_name>.+?)\s+in\s+(?P<city>.+)$')

        split_data['school_name'] = split_data['school_name'].fillna(df_temp[column])
        split_data['city'] = split_data['city'].fillna("Unknown")

        split_data['school_name'] = split_data['school_name'].str.strip()
        split_data['city'] = split_data['city'].str.strip()

        unique_highschools = split_data[['school_name', 'city']].drop_duplicates().reset_index(drop=True)
        unique_highschools['id'] = range(1, len(unique_highschools) + 1) 
        

        highschool_table = unique_highschools.rename(columns={'school_name': 'name'})

        split_data['temp_key'] = split_data['school_name'] + "_" + split_data['city']
        unique_highschools['temp_key'] = unique_highschools['school_name'] + "_" + unique_highschools['city']
        
        mapping_dict = dict(zip(unique_highschools['temp_key'], unique_highschools['id']))
        
        temp_mapped_keys = split_data['temp_key'].map(mapping_dict)
        self._dataframe[new_foreign_key_name] = temp_mapped_keys


        self._dataframe = self._dataframe.drop(column, axis=1)

        return highschool_table[['id', 'name', 'city']], self._dataframe
    

class Season_Cleaner(Data_Cleaner):
    def __init__(self, dataframe):
        super().__init__(dataframe)


    def select_rename(self):
        select_column = ["Season"]
        super().select_columns(select_column)
        column_rename = {
            "Season" : "season_years"
        }
        super().rename_columns(column_rename)

        return self._dataframe
    

class Season_Club_Cleaner(Data_Cleaner):
    def __init__(self, dataframe):
        super().__init__(dataframe)


    def select_rename(self):
        select_column = [
            "Season", 
            "Team", 
            "W", 
            "L", 
            "Finish", 
            "SRS", 
            "Pace",
            "Rel Pace",
            "ORtg",
            "DRtg",
            "Rel ORtg", 
            "Rel DRtg", 
            "Coaches"
            ]
        super().select_columns(select_column)
        column_rename = {
            "Season": "season_id",       
            "Team": "club_id",         
            "W": "win",                
            "L": "loss",                 
            "Finish": "rank",           
            "SRS": "SRS",  
            "Pace" : "pace",
            "Rel Pace" : "relative_pace",
            "Rel ORtg": "relative_ORtg",   
            "Rel DRtg": "relative_DRtg",     
            "Coaches": "coaches"
            }
        super().rename_columns(column_rename)


    def extract_rank(self, column_name = "rank"):
        self._dataframe[column_name] = self._dataframe[column_name].astype(str).str.extract(r'(\d+)')
            
        self._dataframe[column_name] = pd.to_numeric(self._dataframe[column_name], errors='coerce').astype('Int64')
            
        return self._dataframe
    
    
    def remove_trailing_asterisk(self, column_name = "club_id"):
        self._dataframe[column_name] = (
            self._dataframe[column_name]
                .astype(str)
                .str.rstrip('*')  
                .str.strip()       
            )
        return self._dataframe
    

    def fix_season_years_format(self, column_name="season_id"):
  
        self._dataframe[column_name] = self._dataframe[column_name].astype(str).str.strip()
        

        self._dataframe[column_name] = self._dataframe[column_name].str.replace(
            r'(\d{4})-(\d{2})', 
            lambda m: f"{m.group(1)}-{m.group(1)[:2]}{m.group(2)}", 
            regex=True
        )
    
        return self._dataframe     
    
    def extract_coaches_many_to_many(self, column="coaches", team_season_id_column="id"):

        exploded_df = Data_Cleaner.split_and_explode(self._dataframe, column)

        extracted_data = exploded_df[column].str.extract(r'^(?P<coach_name>.+?)\s*\((?P<wins>\d+)-(?P<losses>\d+)\)')

        exploded_df['coach_name'] = extracted_data['coach_name'].fillna(exploded_df[column]).str.strip()
        exploded_df['wins'] = pd.to_numeric(extracted_data['wins']).fillna(0).astype(int)
        exploded_df['losses'] = pd.to_numeric(extracted_data['losses']).fillna(0).astype(int)

        unique_coaches = exploded_df['coach_name'].dropna().unique()
        coaches_table = pd.DataFrame()
        coaches_table["name"] = unique_coaches
        coaches_table["id"] = range(1, len(coaches_table) + 1)

        coach_map = dict(zip(coaches_table["name"], coaches_table["id"]))
        

        bridge_table = pd.DataFrame()
        bridge_table["club_season_id"] = exploded_df[team_season_id_column]
        bridge_table["coach_id"] = exploded_df['coach_name'].map(coach_map)
        bridge_table["wins"] = exploded_df['wins']
        bridge_table["losses"] = exploded_df['losses']

        bridge_table = bridge_table.dropna(subset=["coach_id"])
        bridge_table = bridge_table.drop_duplicates(subset=["club_season_id", "coach_id"]).reset_index(drop=True)
        bridge_table["id"] = range(1, len(bridge_table) + 1)

        if column in self._dataframe.columns:
            self._dataframe = self._dataframe.drop(column, axis=1)

        return coaches_table, bridge_table, self._dataframe
    

class Season_Player_Cleaner(Data_Cleaner):
    def __init__(self, dataframe):
        super().__init__(dataframe)


    def select_rename(self):
        select_column = [
            "Player",         
            "Season",     
            "Rk",          
            "PTS",          
            "G",            
            "MP",           
            "FG",
            "FGA",            
            "AST",           
            "BLK",
            "Awards",
             "GS", "TRB", "STL", "TOV", "PF", "eFG%", "FT%"]                

        super().select_columns(select_column)
        column_rename = {
            "Player": "player_id",
            "Season": "season_id",
            "Rk": "rank",
            "PTS": "pts",
            "G": "game",
            "MP": "minutes_played",
            "FG": "field_goals",
            "FGA" :"Attemps_field_goals",
            "AST": "assists",
            "BLK": "block",
            "GS": "games_started",

            "TRB": "total_rebounds",
            "STL": "steals",
            "TOV": "turnovers",
            "PF": "personal_fouls",
  
            "eFG%": "effective_field_goal_percentage",
            "FT%": "free_throw_percentage"
        }
        
        super().rename_columns(column_rename)

        return self._dataframe
