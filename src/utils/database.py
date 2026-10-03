import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()


def get_database_url():
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )


def get_engine():
    return create_engine(get_database_url())


if __name__ == "__main__":
    try:
        engine = get_engine()

        with engine.connect() as connection:
            print("Connected to PostgreSQL successfully!")

    except Exception as e:
        print("Database connection failed:")
        print(e)