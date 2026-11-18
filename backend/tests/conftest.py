"""Fixture bersama. Modul yang TIDAK ada di paket review (envfile, auth_routes, parsing, resolver) di-stub hanya bila
memang belum ada di proyek Anda; bila sudah ada, versi asli yang dipakai."""
import os
import re
import sys
import types
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/sis")
os.environ.setdefault("JWT_SECRET", "x" * 8 + "Rb7!kQ2#vZ9pLm4$Tn6&Wd1^Hs3*Fg5(" )  # 40 karakter, bukan placeholder


def _missing(name: str) -> bool:
    """Cek lewat berkas (bukan import): mengimpor paket app.engine akan gagal bila submodulnya yang hilang."""
    rel = Path(*name.split("."))
    return not ((BACKEND / rel).with_suffix(".py").exists() or (BACKEND / rel / "__init__.py").exists())


def _stub(name: str, **attrs) -> None:
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod


if _missing("app.envfile"):
    _stub("app.envfile", load_env=lambda: None)

if _missing("app.api.auth_routes"):
    from fastapi import APIRouter

    _stub("app.api.auth_routes", router=APIRouter())

if _missing("app.engine.parsing"):
    def _kelas(t):
        m = re.search(r"XII[ -]([A-Za-z]+)[ -](\d)", t.upper())
        return f"XII-{m.group(1)}-{m.group(2)}" if m else ""

    def _sem(t):
        m = re.search(r"semester (\d)", t.lower())
        return int(m.group(1)) if m else 0

    _stub(
        "app.engine.parsing",
        normalize_kelas=_kelas, parse_semester=_sem, parse_ambang=lambda t: 5, parse_hari=lambda t: "",
        parse_jurusan=lambda t: "", parse_mapel=lambda t, k="", j="": "MTK" if "matematika" in t.lower() else "",
        mentions_unknown_kelas=lambda t: False, outside_scope=lambda t: False,
    )

if _missing("app.engine.resolver"):
    _stub(
        "app.engine.resolver",
        find_siswa_in_text=lambda db, pesan, hint=None: [], find_guru=lambda *a, **k: [],
        find_perusahaan=lambda *a, **k: [], find_ekskul=lambda *a, **k: None,
    )
