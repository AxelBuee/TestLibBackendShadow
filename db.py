from psycopg2 import OperationalError

from sqlmodel import create_engine, SQLModel, Session
from config import Db_Settings
from dotenv import load_dotenv

load_dotenv()

db_settings = Db_Settings()
uri = db_settings.get_db_uri()
engine = create_engine(url=uri, echo=True)
try:
    # Ping the database
    engine.connect()
    print("Connected to the database.")
except OperationalError as e:
    print("Failed to connect to the database:", e)


def get_db():
    with Session(engine) as session:
        yield session


def delete_db_and_tables(engine):
    SQLModel.metadata.drop_all(bind=engine)


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(bind=engine)
