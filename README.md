# SIS - School Intelligence System (SMKN 4 Bandung, kelas XII)

Status: fase **Setup** selesai (database, dataset, kerangka backend). Belum ada: Hybrid Query Engine (Gemini + RAG), frontend.

```
sis/
  docker-compose.yml     db (PostgreSQL 16) + backend (FastAPI)
  .env.example           salin menjadi .env
  database/
    init/                01_schema.sql (21 tabel data), 02_system.sql (users, audit_log, import_batch)
    dataset_bersih/      21 CSV + profil_sekolah.json (kelas XII: 612 siswa, 17 kelas)
    tools/               skrip pembuat dan validator dataset, laporan pembersihan
  backend/
    app/                 FastAPI: auth (JWT, admin/teacher), endpoint data, queries.py (SQL tetap)
    scripts/             import_dataset, seed_users, bootstrap
```

## Cara 1 - Docker (satu perintah)

```bash
cp .env.example .env      # isi POSTGRES_PASSWORD dan JWT_SECRET
docker compose up --build
```

- API + dokumentasi: http://localhost:8000/docs  (health: /api/v1/health)
- PostgreSQL: localhost:5432 (untuk DBeaver; user/password/db dari `.env`)
- Saat pertama jalan, backend membuat skema, memuat dataset, dan membuat 3 admin + 10 teacher.
  Kata sandi awal ada di `backend/seed_output/seed_credentials.txt` (wajib diganti saat login pertama).
- `docker compose down -v` mengosongkan database.

## Cara 2 - Manual (tanpa Docker)

Prasyarat: PostgreSQL 16, Python 3.11+.

```sql
CREATE USER sis WITH PASSWORD 'ganti-ini';
CREATE DATABASE sis OWNER sis;
```

```bash
cp .env.example .env      # isi JWT_SECRET, lalu aktifkan baris DATABASE_URL (sesuaikan kata sandi)
cd backend
python -m venv .venv
.venv\Scripts\activate    # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.import_dataset      # skema + dataset
python -m scripts.seed_users          # 3 admin + 10 teacher -> backend/seed_output/seed_credentials.txt
uvicorn app.main:app --reload --port 8000
```

Muat ulang dari nol (menghapus semua termasuk akun): `python -m scripts.import_dataset --reset`.

## Akun

- 3 admin (`admin1`..`admin3`) dan 10 teacher (`guru01`..`guru10`); kata sandi acak, bukan hardcode.
- 10 guru penerima akun teacher SEMENTARA = wali kelas 10 kelas pertama. Ganti: `python -m scripts.seed_users --nips-file daftar_nip.txt`.

## Endpoint (prefiks /api/v1)

Auth: `POST /auth/login`, `GET /auth/me`, `POST /auth/ganti-password`. Sistem: `GET /health`.
Data: `/kelas`, `/kelas/{kode}/siswa`, `/kelas/{kode}/jadwal`, `/siswa`, `/siswa/{nis}`, `/siswa/{nis}/nilai|kehadiran|pelanggaran` (pelanggaran dicatat di audit_log), `/pkl/penempatan`, `/pkl/perusahaan`, `/ekskul`, `/guru`, `/guru/{nip}/jadwal`, `/sekolah/profil`.
Chat: `POST /chat` (Hybrid Query Engine; semua pertanyaan dicatat).
Admin: `GET/POST /users`, `PATCH /users/{id}`, `GET /admin/audit`, `GET /admin/impor`.

## Cara menjalankan

Lihat `PANDUAN_MENJALANKAN.md` (Docker dan manual, Gemini opsional, cek cepat, troubleshooting).

## Yang sudah diuji dan belum

- Diuji: skema + 21 CSV dimuat tanpa pelanggaran FK (SQLite); semua query dijalankan terhadap data nyata; Hybrid Query Engine lolos ~20 uji (mode aturan, tanpa Gemini); semua Python lolos kompilasi; sintaks TypeScript frontend lolos.
- Belum diuji: PostgreSQL, Docker build, FastAPI/bcrypt/psycopg saat berjalan, skrip impor/seed, `npm install`/`next build`, tampilan frontend di browser, dan Gemini asli. Kemungkinan ada galat kecil saat pertama dijalankan; kirim pesan galatnya untuk diperbaiki.
