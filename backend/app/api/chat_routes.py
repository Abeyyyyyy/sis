"""POST /chat: pintu masuk Hybrid Query Engine. Semua pertanyaan dicatat di audit_log."""
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import Connection, text

from .. import engine, queries
from ..auth import current_user
from ..db import get_conn
from ..engine.core import bound, plain

router = APIRouter(tags=["chat"])


class SaDb:
    """Adaptor SQLAlchemy untuk antarmuka Db milik engine."""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def rows(self, sql: str, **params) -> list[dict]:
        result = self.conn.execute(text(sql), bound(sql, params)).mappings().all()
        return [{k: plain(v) for k, v in row.items()} for row in result]


class ChatIn(BaseModel):
    pesan: str = Field(min_length=1, max_length=500)
    sesi_id: str | None = None


@router.post("/chat")
def chat(body: ChatIn, user: dict = Depends(current_user), conn: Connection = Depends(get_conn)):
    out = engine.answer(SaDb(conn), body.pesan)
    conn.execute(
        text(queries.AUDIT_CHAT),
        {
            "user_id": user["id"],
            "aksi": "chat_data_sensitif" if out["sensitif"] else "chat",
            "pertanyaan": body.pesan,
            "intent": json.dumps(out["intent"], ensure_ascii=False),
            "tabel": ",".join(out["sumber"]),
            "status": "perlu_klarifikasi" if out["butuh_klarifikasi"] else "ok",
        },
    )
    return {
        "jawaban": out["jawaban"],
        "tabel": out["tabel"],
        "sumber": out["sumber"],
        "intent": out["intent"],
        "mode": out["mode"],
        "sensitif": out["sensitif"],
        "contoh": out["contoh"],
    }
