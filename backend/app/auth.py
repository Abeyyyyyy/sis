"""Autentikasi: bcrypt + JWT. Hanya dua peran: admin dan teacher."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text

from . import queries
from .config import settings
from .db import engine

ROLES = ("admin", "teacher")
_bearer = HTTPBearer(auto_error=False)
MAX_PASSWORD_BYTES = 72  # batas bcrypt; bcrypt>=5 melempar ValueError bila lebih


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def validate_new_password(password: str, username: str = "") -> str | None:
    """Pesan galat bila kata sandi baru tidak layak; None bila lolos. Panggil dari POST /auth/ganti-password."""
    if len(password) < 10:
        return "Kata sandi minimal 10 karakter."
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return f"Kata sandi terlalu panjang (maksimal {MAX_PASSWORD_BYTES} byte)."
    if username and username.lower() in password.lower():
        return "Kata sandi tidak boleh memuat username."
    return None


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _error(code: int, kode: str, pesan: str) -> HTTPException:
    return HTTPException(status_code=code, detail={"code": kode, "message": pesan, "details": None})


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Pengguna dari token. TIDAK menahan koneksi DB sesudah selesai (aman dipakai di endpoint yang memanggil Gemini).

    Peran selalu diambil dari database, bukan dari klaim token, sehingga perubahan peran/penonaktifan langsung berlaku.
    """
    if creds is None:
        raise _error(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Token tidak ada; silakan login.")
    try:
        data = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"], options={"require": ["exp", "sub"]})
        user_id = int(data["sub"])
    except (jwt.PyJWTError, ValueError, TypeError):
        raise _error(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Token tidak valid atau kedaluwarsa.")
    with engine.connect() as conn:  # koneksi pendek, langsung kembali ke kolam
        user = conn.execute(text(queries.USER_BY_ID), {"id": user_id}).mappings().first()
    if user is None or not user["aktif"]:
        raise _error(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Akun tidak ditemukan atau dinonaktifkan.")
    return dict(user)


def active_user(user: dict = Depends(current_user)) -> dict:
    """Seperti current_user, tetapi menolak (403) selama kata sandi sementara belum diganti.

    Pakai ini untuk SEMUA endpoint data/chat/admin. Hanya /auth/me, /auth/ganti-password, dan /auth/logout
    yang boleh memakai current_user langsung. Sebelumnya kewajiban ganti sandi hanya dicek di frontend.
    """
    if user.get("wajib_ganti_password"):
        raise _error(status.HTTP_403_FORBIDDEN, "PASSWORD_CHANGE_REQUIRED", "Ganti kata sandi sementara Anda terlebih dahulu.")
    return user


def require_admin(user: dict = Depends(active_user)) -> dict:
    if user["role"] != "admin":
        raise _error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Hanya admin yang boleh mengakses ini.")
    return user


_ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_password(length: int = 12) -> str:
    import secrets

    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
