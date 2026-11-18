"""Katalog intent + pemahaman pertanyaan.

Dua jalur menghasilkan intent JSON yang SAMA bentuknya:
  1. Gemini (bila GEMINI_API_KEY diisi) -> JSON -> divalidasi terhadap katalog ini.
  2. Parser aturan (kata kunci) bila Gemini tidak aktif atau gagal.
AI tidak pernah membuat SQL; ia hanya memilih intent dan mengisi parameter.
"""
import json
import re

from . import gemini
from .parsing import (
    normalize_kelas,
    parse_ambang,
    parse_hari,
    parse_jurusan,
    parse_mapel,
    parse_semester,
)

INTENTS = {
    "cari_siswa": "Mencari siswa berdasarkan nama/NIS atau melihat daftar siswa satu kelas. params: siswa, kelas",
    "profil_siswa": "Profil satu siswa (kelas, wali kelas, PKL, ekskul). params: siswa",
    "nilai_siswa": "Nilai satu siswa. params: siswa, semester (1-6, opsional), mapel (opsional)",
    "ranking_kelas": "Peringkat rata-rata nilai dalam satu kelas. params: kelas, semester, mapel (opsional)",
    "siswa_di_bawah_kkm": "Siswa dengan nilai di bawah KKM. params: kelas (opsional), semester, mapel (opsional)",
    "rekap_kehadiran": "Rekap sakit/izin/alpha/hadir satu siswa atau satu kelas. params: siswa atau kelas, semester (opsional)",
    "siswa_alpha_tinggi": "Siswa dengan alpha tinggi. params: kelas (opsional), semester, ambang (jumlah hari alpha minimal)",
    "pelanggaran_siswa": "Catatan pelanggaran satu siswa atau satu kelas. params: siswa atau kelas",
    "jadwal_kelas": "Jadwal pelajaran satu kelas. params: kelas, hari (opsional)",
    "jadwal_guru": "Jadwal mengajar satu guru. params: guru",
    "info_wali_kelas": "Wali kelas suatu kelas, atau kelas yang diwalikan seorang guru. params: kelas atau guru",
    "penempatan_pkl": "Penempatan PKL satu siswa, satu kelas, atau satu perusahaan. params: siswa, kelas, atau perusahaan",
    "info_ekskul": "Info ekstrakurikuler, atau anggota satu ekskul. params: ekskul (opsional), siswa (opsional)",
    "info_sekolah": "Profil sekolah, visi misi, tata tertib, sanksi, prestasi, fasilitas, mitra industri. params: topik",
}
PARAM_KEYS = {"siswa", "kelas", "semester", "mapel", "hari", "guru", "perusahaan", "ekskul", "ambang", "topik"}

CONTOH = [
    "Siapa wali kelas XII TITL 6?",
    "Siswa XII RPL 2 yang nilainya di bawah KKM semester 5",
    "Siapa saja yang alpha lebih dari 5 hari semester ini?",
    "Di mana Aditya Ramadhan PKL?",
    "Apa sanksi untuk pelanggaran tingkat sedang?",
]


def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text))


def rule_intent(pesan: str) -> dict:
    """Parser kata kunci -> {"intent", "params"}. Nama orang diselesaikan kemudian oleh resolver."""
    low = pesan.lower()
    kelas = normalize_kelas(pesan)
    params: dict = {}
    if kelas:
        params["kelas"] = kelas
    sem = parse_semester(pesan)
    if sem:
        params["semester"] = sem
    hari = parse_hari(pesan)
    if hari:
        params["hari"] = hari
    mapel = parse_mapel(pesan, kelas, parse_jurusan(pesan))
    if mapel:
        params["mapel"] = mapel

    def out(name: str) -> dict:
        return {"intent": name, "params": params}

    if _has(low, r"\bwali\b"):
        return out("info_wali_kelas")
    if _has(low, r"\bjadwal\b|\bmengajar\b"):
        return out("jadwal_kelas" if kelas else "jadwal_guru")
    if _has(low, r"\bpkl\b|magang|prakerin"):
        return out("penempatan_pkl")
    if _has(low, r"ekskul|ekstrakurikuler|\bekstra\b|organisasi"):
        return out("info_ekskul")
    if _has(low, r"sanksi|tata tertib|peraturan|aturan|seragam|\bvisi\b|\bmisi\b|prestasi|akreditasi|fasilitas|"
                 r"sejarah sekolah|alamat sekolah|profil sekolah|kemitraan|iduka|motto|jurusan apa|program keahlian"):
        params["topik"] = pesan
        return out("info_sekolah")
    if _has(low, r"pelanggaran|melanggar|\bpoin\b"):
        return out("pelanggaran_siswa")
    if _has(low, r"\balpha\b|\balpa\b|bolos"):
        params["ambang"] = parse_ambang(pesan)
        return out("siswa_alpha_tinggi")
    if _has(low, r"kehadiran|absensi|presensi|\bhadir\b|\bsakit\b|\bizin\b"):
        return out("rekap_kehadiran")
    if _has(low, r"kkm|remedial|tidak tuntas|belum tuntas|di bawah"):
        return out("siswa_di_bawah_kkm")
    if _has(low, r"ranking|peringkat|tertinggi|terendah|terbaik|juara|teratas|terburuk"):
        return out("ranking_kelas")
    if _has(low, r"\bnilai|rapor|rata-rata|rata rata"):
        return out("nilai_siswa")
    if _has(low, r"\bcari\b|\bsiapa\b|profil|biodata|\bdata\b|\binfo"):
        return out("profil_siswa" if not kelas else "cari_siswa")
    return out("profil_siswa")


def _system_prompt() -> str:
    daftar = "\n".join(f"- {k}: {v}" for k, v in INTENTS.items())
    return (
        "Kamu adalah penerjemah pertanyaan guru SMKN 4 Bandung (khusus kelas XII) menjadi JSON intent.\n"
        "Pilih TEPAT SATU intent dari daftar, isi params yang disebut pengguna, jangan mengarang nilai.\n"
        f"Daftar intent:\n{daftar}\n\n"
        "Format keluaran (hanya JSON): {\"intent\": \"<nama>\", \"params\": {\"siswa\": \"...\", \"kelas\": \"XII TITL 6\", "
        "\"semester\": 5, ...}}. Kelas ditulis seperti 'XII TITL 6'. Jika pertanyaan tidak cocok dengan intent mana pun, "
        "keluarkan {\"intent\": \"tidak_dikenali\", \"params\": {}}. Jangan membuat SQL."
    )


def gemini_intent(pesan: str) -> dict | None:
    raw = gemini.generate(_system_prompt(), pesan, json_mode=True)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    name = data.get("intent") if isinstance(data, dict) else None
    if name == "tidak_dikenali":
        return {"intent": "tidak_dikenali", "params": {}}
    if name not in INTENTS:
        return None
    raw_params = data.get("params") if isinstance(data.get("params"), dict) else {}
    params = {k: v for k, v in raw_params.items() if k in PARAM_KEYS and v not in (None, "", [])}
    for key in ("semester", "ambang"):
        if key in params:
            try:
                params[key] = int(params[key])
            except (TypeError, ValueError):
                params.pop(key)
    if "semester" in params and not 1 <= params["semester"] <= 6:
        params.pop("semester")
    return {"intent": name, "params": params}


def understand(pesan: str) -> tuple[dict, str]:
    """Kembalikan (intent_json, mode). mode = 'gemini' atau 'aturan'. Parameter dasar selalu dilengkapi dari teks."""
    from_rules = rule_intent(pesan)
    parsed = gemini_intent(pesan) if gemini.enabled() else None
    if parsed is None:
        return from_rules, "aturan"
    params = dict(parsed["params"])
    kelas = normalize_kelas(str(params.get("kelas", ""))) or from_rules["params"].get("kelas")
    if kelas:
        params["kelas"] = kelas
    else:
        params.pop("kelas", None)
    for key in ("semester", "hari", "mapel", "ambang"):
        if key not in params and key in from_rules["params"]:
            params[key] = from_rules["params"][key]
    return {"intent": parsed["intent"], "params": params}, "gemini"
