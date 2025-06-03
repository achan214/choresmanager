from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from src import config

Base = declarative_base()

connection_url = config.get_settings().POSTGRES_URI
engine = create_engine(connection_url, pool_pre_ping=True)
