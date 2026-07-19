import os
from pathlib import Path
from sqlalchemy import create_engine , URL
from dotenv import load_dotenv


class DatabaseConnector:
    def __init__(self, env_path="../.env"):
        self.env_path = Path(env_path)
        self.engine = None
        
        
    def load_environment(self):
         load_dotenv(dotenv_path = self.env_path)
 
 
    def create_connection(self):
        self.load_environment()
        
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_NAME")

        connection_format = (f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}")

        self.engine = create_engine(connection_format)
        return self.engine