"""Pengaturan dari environment (.env)."""
import os
from pathlib import Path

from .envfile import load_env

load_env()


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Variabel environment {name} belum diisi (lihat .env.example).")
    return value


class Settings:
    database_url: str = _required("DATABASE_URL")  # postgresql+psycopg://user:pass@host:5432/sis
    jwt_secret: str = _required("JWT_SECRET")
    jwt_expire_minutes: int = int(os.environ.get("JWT_EXPIRE_MINUTES", "120"))
    cors_origins: list[str] = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()
    ]
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    dataset_dir: str = os.environ.get(
        "DATASET_DIR", str(Path(__file__).resolve().parents[2] / "database" / "dataset_bersih")
    )


settings = Settings()
