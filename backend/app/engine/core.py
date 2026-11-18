"""Bagian dasar engine: antarmuka database, hasil query, dan helper umum. Hanya pustaka standar."""
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol

_BIND = re.compile(r"(?<!:):([a-zA-Z_]\w*)")


def bound(sql: str, params: dict) -> dict:
    """Hanya parameter yang benar-benar dipakai SQL (parameter lebih diabaikan)."""
    names = set(_BIND.findall(sql))
    return {k: v for k, v in params.items() if k in names}


def plain(value: Any) -> Any:
    """Ubah tipe database ke tipe JSON biasa."""
    if isinstance(value, Decimal):
        f = float(value)
        return int(f) if f.is_integer() else round(f, 2)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


class Db(Protocol):
    def rows(self, sql: str, **params: Any) -> list[dict]: ...


@dataclass
class Result:
    """Hasil satu intent: teks jawaban baku (template), tabel, dan metadata."""

    jawaban: str
    kolom: list[str] = field(default_factory=list)
    baris: list[list[Any]] = field(default_factory=list)
    sumber: list[str] = field(default_factory=list)  # tabel yang dibaca
    butuh_klarifikasi: bool = False  # True bila pertanyaan kurang jelas / ambigu
    sensitif: bool = False  # True bila menyentuh data pelanggaran

    def tabel(self) -> dict | None:
        return {"kolom": self.kolom, "baris": self.baris} if self.kolom and self.baris else None


def table_from(rows: list[dict], columns: list[tuple[str, str]]) -> tuple[list[str], list[list[Any]]]:
    """columns = [(kunci_dict, judul_kolom)]"""
    return [t for _, t in columns], [[r.get(k) for k, _ in columns] for r in rows]


def fmt_num(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return str(v)
