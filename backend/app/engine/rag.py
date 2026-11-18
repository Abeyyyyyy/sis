"""RAG sederhana atas profil_sekolah.json (pencarian leksikal).

Profil sekolah hanya ~6.600 karakter, jadi pencarian kata kunci berbobot IDF sudah cukup untuk MVP.
Antarmuka `retrieve()` sengaja dibuat sama dengan yang nanti dipakai ChromaDB: tinggal ganti isi fungsinya.
"""
import json
import math
import re
from functools import lru_cache
from pathlib import Path

from ..config import settings

_STOP = {"yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "itu", "ini", "apa", "siapa", "adalah", "saja", "tentang",
         "sekolah", "smkn", "bandung", "bagaimana", "berapa", "ada", "atau", "para", "kami", "kita", "saya"}
_LABELS = {
    "identitas_sekolah": "Identitas sekolah", "sejarah": "Sejarah", "visi_dan_misi": "Visi dan misi",
    "program_dan_konsentrasi_keahlian": "Program keahlian", "sarana_dan_fasilitas": "Sarana dan fasilitas",
    "ekstrakurikuler_dan_organisasi": "Ekstrakurikuler dan organisasi", "peraturan_dan_tata_tertib": "Peraturan dan tata tertib",
    "prestasi_dan_mitra_industri": "Prestasi dan mitra industri",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) >= 3 and t not in _STOP]


def _text(node) -> str:
    if isinstance(node, dict):
        return "; ".join(f"{k.replace('_', ' ')}: {_text(v)}" for k, v in node.items())
    if isinstance(node, list):
        return "; ".join(_text(x) for x in node)
    return str(node)


def _flatten(path: list[str], node, out: list[tuple[str, str]]) -> None:
    label = " > ".join(_LABELS.get(p, p.replace("_", " ")) for p in path)
    if isinstance(node, dict):
        # tingkat dua dijadikan potongan sendiri agar pencarian lebih tepat
        for k, v in node.items():
            if len(path) < 2:
                _flatten(path + [k], v, out)
            else:
                out.append((label, f"{k.replace('_', ' ')}: {_text(v)}"))
    elif isinstance(node, list) and len(path) <= 2:
        for item in node:
            out.append((label, _text(item)))
    else:
        out.append((label, _text(node)))


@lru_cache(maxsize=1)
def chunks() -> list[tuple[str, str]]:
    path = Path(settings.dataset_dir) / "profil_sekolah.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[tuple[str, str]] = []
    for key, value in data.items():
        _flatten([key], value, out)
    return out


def retrieve(query: str, k: int = 3) -> list[tuple[str, str]]:
    """Potongan teks paling relevan: [(bagian, isi)]. Kosong bila tidak ada kata yang cocok."""
    docs = chunks()
    q = set(_tokens(query))
    if not q:
        return []
    doc_tokens = [set(_tokens(f"{label} {text}")) for label, text in docs]
    n = len(docs)
    idf = {t: math.log(1 + n / (1 + sum(t in d for d in doc_tokens))) for t in q}
    scored = []
    for (label, text), toks in zip(docs, doc_tokens):
        score = sum(idf[t] for t in q if t in toks)
        if score > 0:
            scored.append((score, label, text))
    scored.sort(key=lambda x: -x[0])
    return [(label, text) for _, label, text in scored[:k]]
