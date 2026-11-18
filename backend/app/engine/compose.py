"""Penyusun jawaban + validator output.

Jawaban baku dari handler selalu tersedia. Bila Gemini aktif, ia diminta merangkai ulang jawaban itu dengan bahasa
yang lebih natural. Rangkaian Gemini dipakai HANYA bila semua angka di dalamnya ada di data (jawaban baku, tabel,
atau pertanyaan); jika tidak, jawaban baku yang dipakai. NIS dan NISN tidak pernah dikirim ke Gemini.
"""
import json
import re

from . import gemini
from .core import Result

_NUM = re.compile(r"\d+(?:[.,]\d+)*")
_PRIVATE_COLS = {"nis", "nisn"}
_SYSTEM = (
    "Kamu asisten guru SMKN 4 Bandung. Tulis jawaban singkat (maksimal 4 kalimat) dalam bahasa Indonesia yang ramah, "
    "HANYA berdasarkan data yang diberikan. Jangan menambah angka, nama, atau fakta baru. Jangan menyimpulkan karakter siswa. "
    "Jangan mengulang seluruh tabel; tabel ditampilkan terpisah."
)


def _norm_num(s: str) -> str:
    s = s.replace(",", ".")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def numbers(text: str) -> set[str]:
    return {_norm_num(n) for n in _NUM.findall(text)}


def allowed_numbers(question: str, res: Result) -> set[str]:
    allowed = numbers(question) | numbers(res.jawaban)
    for row in res.baris:
        for cell in row:
            allowed |= numbers(str(cell))
    return allowed


def valid_output(candidate: str, question: str, res: Result) -> bool:
    if not candidate or len(candidate) > 1200:
        return False
    return numbers(candidate) <= allowed_numbers(question, res)


def compose(question: str, res: Result) -> tuple[str, str]:
    """Kembalikan (teks_jawaban, mode)."""
    if res.butuh_klarifikasi or not gemini.enabled():
        return res.jawaban, "aturan"
    cols = [i for i, c in enumerate(res.kolom) if c.lower() not in _PRIVATE_COLS]
    data = {
        "kolom": [res.kolom[i] for i in cols],
        "baris": [[row[i] for i in cols] for row in res.baris[:25]],
        "jumlah_baris_total": len(res.baris),
    }
    prompt = (
        f"Pertanyaan guru: {question}\n\nJawaban baku (fakta benar): {res.jawaban}\n\n"
        f"Data tabel: {json.dumps(data, ensure_ascii=False)}\n\nTulis jawaban singkat."
    )
    candidate = gemini.generate(_SYSTEM, prompt)
    if candidate and valid_output(candidate.strip(), question, res):
        return candidate.strip(), "gemini"
    return res.jawaban, "aturan"
