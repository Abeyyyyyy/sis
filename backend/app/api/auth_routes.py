from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from .. import queries
from ..auth import create_token, current_user, hash_password, verify_password
from ..db import get_conn

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str
    password: str


class GantiPasswordIn(BaseModel):
    password_lama: str
    password_baru: str = Field(min_length=8)


def _public(user: dict) -> dict:
    return {k: user[k] for k in ("id", "username", "nama", "nip", "role", "wajib_ganti_password")}


@router.post("/login")
def login(body: LoginIn, conn: Connection = Depends(get_conn)):
    user = conn.execute(text(queries.USER_BY_USERNAME), {"username": body.username}).mappings().first()
    if user is None or not user["aktif"] or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, {"code": "UNAUTHORIZED", "message": "Username atau kata sandi salah.", "details": None})
    return {"access_token": create_token(user["id"], user["role"]), "token_type": "bearer", "user": _public(dict(user))}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return _public(user)


@router.post("/ganti-password")
def ganti_password(body: GantiPasswordIn, user: dict = Depends(current_user), conn: Connection = Depends(get_conn)):
    row = conn.execute(text(queries.USER_BY_USERNAME), {"username": user["username"]}).mappings().first()
    if not verify_password(body.password_lama, row["password_hash"]):
        raise HTTPException(400, {"code": "BAD_REQUEST", "message": "Kata sandi lama salah.", "details": None})
    conn.execute(text(queries.USER_SET_PASSWORD), {"hash": hash_password(body.password_baru), "id": user["id"]})
    return {"status": "ok"}
