import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def get_db_connection():
    """Create and return a connection to the configured PostgreSQL database."""
    db_password = os.getenv("DB_PASSWORD")
    if not db_password:
        raise RuntimeError("DB_PASSWORD is missing from .env")

    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "rag_db"),
        user=os.getenv("DB_USER", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        password=db_password,
    )
