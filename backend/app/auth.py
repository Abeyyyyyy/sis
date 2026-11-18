"""Autentikasi: bcrypt + JWT. Hanya dua peran: admin dan teacher."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Connection, text

from . import queries
from .config import settings
from .db import get_conn

ROLES = ("admin", "teacher")
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def create_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _error(code: int, kode: str, pesan: str) -> HTTPException:
    return HTTPException(status_code=code, detail={"code": kode, "message": pesan, "details": None})


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer), conn: Connection = Depends(get_conn)
) -> dict:
    if creds is None:
        raise _error(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Token tidak ada; silakan login.")
    try:
        data = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise _error(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Token tidak valid atau kedaluwarsa.")
    user = conn.execute(text(queries.USER_BY_ID), {"id": int(data["sub"])}).mappings().first()
    if user is None or not user["aktif"]:
        raise _error(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Akun tidak ditemukan atau dinonaktifkan.")
    return dict(user)


def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":
        raise _error(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "Hanya admin yang boleh mengakses ini.")
    return user


_ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_password(length: int = 12) -> str:
    import secrets

    return "".join(secrets.choice(_ALPHABET) for _ in range(length))
