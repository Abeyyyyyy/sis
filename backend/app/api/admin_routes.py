"""Endpoint khusus admin: akun, audit log, riwayat impor."""
import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from .. import queries
from ..auth import hash_password, new_password, require_admin
from ..db import get_conn

router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin)])


def _err(code: int, kode: str, pesan: str) -> HTTPException:
    return HTTPException(code, {"code": kode, "message": pesan, "details": None})


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nama: str = Field(min_length=1, max_length=120)
    role: Literal["admin", "teacher"]
    nip: str | None = None


class UserPatch(BaseModel):
    aktif: bool | None = None
    reset_password: bool = False


@router.get("/users")
def daftar_user(conn: Connection = Depends(get_conn)):
    return {"data": [dict(r) for r in conn.execute(text(queries.USERS_LIST)).mappings().all()]}


@router.post("/users", status_code=201)
def buat_user(body: UserIn, conn: Connection = Depends(get_conn)):
    if not re.fullmatch(r"[a-zA-Z0-9._-]+", body.username):
        raise _err(422, "VALIDATION_ERROR", "Username hanya boleh huruf, angka, titik, garis bawah, dan strip.")
    if conn.execute(text(queries.USER_BY_USERNAME), {"username": body.username}).first():
        raise _err(409, "CONFLICT", "Username sudah dipakai.")
    if body.nip and not conn.execute(text("SELECT 1 FROM guru WHERE nip = :nip"), {"nip": body.nip}).first():
        raise _err(422, "VALIDATION_ERROR", "NIP tidak ada di data guru.")
    password = new_password()
    new_id = conn.execute(
        text(queries.USER_INSERT),
        {"username": body.username, "nama": body.nama, "nip": body.nip, "role": body.role, "hash": hash_password(password)},
    ).scalar_one()
    # kata sandi awal hanya ditampilkan sekali ini
    return {"id": new_id, "username": body.username, "role": body.role, "password_awal": password}


@router.patch("/users/{user_id}")
def ubah_user(user_id: int, body: UserPatch, conn: Connection = Depends(get_conn)):
    if not conn.execute(text(queries.USER_BY_ID), {"id": user_id}).first():
        raise _err(404, "NOT_FOUND", "Akun tidak ditemukan.")
    out: dict = {"id": user_id}
    if body.aktif is not None:
        conn.execute(text(queries.USER_UPDATE_AKTIF), {"aktif": body.aktif, "id": user_id})
        out["aktif"] = body.aktif
    if body.reset_password:
        password = new_password()
        conn.execute(text(queries.USER_RESET_PASSWORD), {"hash": hash_password(password), "id": user_id})
        out["password_baru"] = password
    return out


@router.get("/admin/audit")
def audit(
    username: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_conn),
):
    rows = conn.execute(
        text(queries.AUDIT_LIST), {"username": username, "limit": page_size, "offset": (page - 1) * page_size}
    ).mappings().all()
    return {"data": [dict(r) for r in rows], "meta": {"page": page, "page_size": page_size}}


@router.get("/admin/impor")
def riwayat_impor(conn: Connection = Depends(get_conn)):
    return {"data": [dict(r) for r in conn.execute(text(queries.IMPORT_LIST)).mappings().all()]}
