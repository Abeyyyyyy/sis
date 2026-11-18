"""Hybrid Query Engine: pertanyaan -> intent JSON -> validasi/resolver -> query tetap atau RAG -> jawaban."""
from . import handlers
from .compose import compose
from .core import Db
from .intents import CONTOH, understand
from .parsing import mentions_unknown_kelas, outside_scope


def answer(db: Db, pesan: str) -> dict:
    """Jawab satu pertanyaan. Mengembalikan dict siap dikirim sebagai JSON (lihat dokumen 03, POST /chat)."""
    pesan = " ".join(pesan.split())
    if outside_scope(pesan):
        return {
            "jawaban": "Data yang tersedia saat ini baru kelas XII. Kelas X dan XI akan menyusul.",
            "tabel": None, "sumber": [], "intent": {"intent": "di_luar_cakupan", "params": {}},
            "mode": "aturan", "sensitif": False, "butuh_klarifikasi": False, "contoh": CONTOH,
        }
    intent, mode_intent = understand(pesan)
    if mentions_unknown_kelas(pesan) and intent["intent"] not in ("tidak_dikenali",):
        intent["params"].pop("kelas", None)
    result = handlers.run(db, intent, pesan)
    teks, mode_jawaban = compose(pesan, result)
    teks = teks.replace("..", ".")  # gelar berakhir titik (S.Pd.) + titik kalimat
    return {
        "jawaban": teks,
        "tabel": result.tabel(),
        "sumber": result.sumber,
        "intent": intent,
        "mode": "gemini" if "gemini" in (mode_intent, mode_jawaban) else "aturan",
        "sensitif": result.sensitif,
        "butuh_klarifikasi": result.butuh_klarifikasi,
        "contoh": CONTOH if result.butuh_klarifikasi else [],
    }
