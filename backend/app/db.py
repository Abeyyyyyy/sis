"""Koneksi database (SQLAlchemy Core + psycopg)."""
from collections.abc import Iterator

from sqlalchemy import Connection, create_engine

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=10,
    pool_timeout=10,  # gagal cepat (bukan 30 dtk) bila kolam habis
    connect_args={
        "connect_timeout": 5,  # jangan menggantung bila database tidak terjangkau
        "options": "-c statement_timeout=10000",  # query liar dihentikan server setelah 10 dtk
    },
)


def get_conn() -> Iterator[Connection]:
    """Dependency FastAPI: satu koneksi per request; commit bila berhasil, rollback bila ada exception.

    Jangan dipakai di endpoint yang memanggil layanan eksternal (Gemini): koneksi akan tertahan selama
    panggilan jaringan. Pakai `with engine.begin()` pendek di sekitar query saja (lihat chat_routes.py).
    """
    with engine.begin() as conn:
        yield conn
