from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

from .models import Base

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        
        USER = os.getenv("DB_USER")
        PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
        HOST = os.getenv("DB_HOST")
        PORT = os.getenv("DB_PORT", "3306") 
        DB_NAME = os.getenv("DB_NAME")

        self.DATABASE_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
        self.engine = create_engine(self.DATABASE_URL, echo=True)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):

        Base.metadata.create_all(self.engine)

    def insert_dataframe(self, df, table_name):
        try:
            df.to_sql(
                name=table_name,
                con=self.engine, 
                if_exists='append', 
                index=False         
            )
        except Exception as e:
            print(f"Error inserting data into table {table_name}: {e}")
            raise e