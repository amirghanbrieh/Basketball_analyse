import pandas as pd


class NBADataLoader:
    def __init__(self, engine):
        self.engine = engine


    def load_dataframe(self, query):
        df = pd.read_sql(query, self.engine)
        return df


    def load_agility_data(self, query_agility):
        df = self.load_dataframe(query_agility)
        return df


    def load_intrinsic_data(self, query_intrinsic):
        df = self.load_dataframe(query_intrinsic)
        return df
