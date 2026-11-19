# School Intelligence System (SIS) - SMKN 4 Bandung

Sistem kecerdasan institusi dan ruang kerja analitik berbasis AI untuk SMKN 4 Bandung, menggabungkan **Hybrid Query Engine (Gemini 3.5 Flash Lite + RAG)**, **PostgreSQL 16**, dan **Next.js**.

---

## Prasyarat & Pilihan Metode Menjalankan

Pilih **Jalur A (Docker / Kontainer)** atau **Jalur B (Windows Native / Skrip)** sesuai kondisi komputer Anda:

| Jalur | Target Pengguna | Prasyarat yang Wajib Ada | Keunggulan Utama |
| :--- | :--- | :--- | :--- |
| **Jalur A: Docker** *(Direkomendasikan)* | Komputer baru / multi-OS | Git, Docker Desktop | Tanpa install runtime lokal (Python, Node, PostgreSQL sudah terisolasi di kontainer) |
| **Jalur B: Skrip Native** | Windows tanpa Docker | Git, Python 3.11+, Node.js 18+, PostgreSQL 16 / WSL | Eksekusi native yang ringan, setup otomatis sekali klik |

---

## Jalur A: Menjalankan Menggunakan Docker (Kontainer)

Metode paling praktis untuk instalasi baru atau lingkungan lintas platform tanpa perlu menginstal dependensi bahasa pemrograman di komputer lokal.

### 1. Prasyarat
- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (pastikan aplikasi Docker Desktop dalam status *running*)

### 2. Langkah Menjalankan
1. Buka terminal dan **arahkan direktori kerja ke folder root proyek**:
   ```bash
   cd path/ke/folder/sis
   ```
2. Salin berkas konfigurasi environment dari template:
   ```bash
   cp .env.example .env
   # Di Windows PowerShell: Copy-Item .env.example .env
   ```
3. Bangun dan jalankan seluruh layanan (Database, Backend, dan Frontend) dengan satu perintah:
   ```bash
   docker compose up --build
   ```
4. Buka aplikasi di peramban:
   - **Aplikasi Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Dokumentasi Interaktif API**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Pemeriksaan Kesehatan Sistem**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

*Untuk menghentikan layanan:* Tekan `Ctrl + C` lalu ketik `docker compose down`. Untuk mengosongkan dan mereset database dari nol: `docker compose down -v`.

---

## Jalur B: Menjalankan di Windows Native (`setup.bat` & `run.bat`)

Metode untuk pengguna Windows yang tidak menggunakan Docker Desktop.

### 1. Prasyarat
Pastikan tiga runtime berikut sudah terinstal di komputer sebelum memulai:
1. **Python 3.11 atau lebih baru**: Unduh dari [python.org](https://www.python.org/downloads/).
   > **PENTING**: Wajib mencentang kotak **"Add Python to PATH"** saat awal instalasi.
2. **Node.js (18 LTS atau 20+)**: Unduh dari [nodejs.org](https://nodejs.org/).
3. **PostgreSQL 16**: Terinstal secara native di Windows atau melalui WSL Ubuntu.

### 2. Inisialisasi Pertama Kali (`setup.bat`)
1. Buka File Explorer, masuk ke folder proyek `SIS`, lalu klik dua kali berkas:
   ```text
   setup.bat
   ```
2. Skrip otomatis akan:
   - Memeriksa dan membuat berkas `.env` jika belum tersedia.
   - Membuat virtual environment Python (`backend/.venv`) dan memasang dependensi backend.
   - Memasang dependensi frontend (`npm install`).
   - Memverifikasi database, menyesuaikan host IP WSL secara dinamis, dan memuat skema beserta dataset (21 tabel, 56.071 baris).
   - Menghasilkan berkas peluncur `run.bat`, kemudian menghapus berkas `setup.bat` secara mandiri (*self-destruct*).

### 3. Menjalankan Sehari-hari (`run.bat`)
Setelah inisialisasi awal selesai, jalankan seluruh layanan kapan saja hanya dengan mengklik dua kali:
```text
run.bat
```
Skrip ini akan otomatis menyalakan PostgreSQL di background, FastAPI Backend (`:8000`), dan Next.js Frontend (`:3000`).

---

## Akun Pengguna

Sistem menyediakan 13 akun bawaan (3 akun Administrator dan 10 akun Guru).

Demi keamanan dan privasi, rincian kredensial akun awal **tidak dicantumkan di repositori publik**. Kredensial awal hanya dihasilkan secara lokal pada saat instalasi pertama dan disimpan di direktori lokal:
```text
backend/seed_output/seed_credentials.txt
```
*(Direktori ini otomatis diabaikan oleh Git melalui `.gitignore`).*

Setiap pengguna diwajibkan memperbarui kata sandi pada saat pertama kali masuk ke sistem.


---

## Tumpukan Teknologi & Arsitektur

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons.
- **Backend**: FastAPI, Uvicorn, SQLAlchemy 2, Psycopg 3, Pydantic 2, PyJWT.
- **AI Engine**: Hybrid Query Engine ditenagai oleh Google Gemini (`gemini-3.5-flash-lite`) dan RAG Leksikal BM25/IDF atas dokumen profil sekolah.
- **Database**: PostgreSQL 16 (21 tabel data akademik, 3 tabel sistem & audit).
