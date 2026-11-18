"""Koneksi database (SQLAlchemy Core + psycopg)."""
from collections.abc import Iterator

from sqlalchemy import Connection, create_engine

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


def get_conn() -> Iterator[Connection]:
    """Dependency FastAPI: satu koneksi per request; commit bila berhasil."""
    with engine.begin() as conn:
        yield conn
