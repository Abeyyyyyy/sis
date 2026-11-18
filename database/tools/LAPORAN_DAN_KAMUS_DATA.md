# Dataset Bersih SIS SMKN 4 Bandung — Kelas XII

Cakupan: 17 kelas XII (RPL 3, DKV 2, TITL 6, TOI 3, TAV 3), 612 siswa (36/kelas), 47 guru.
Format: CSV UTF-8 (siap `COPY` ke PostgreSQL) + `dataset_bersih.xlsx` (untuk dibaca manusia) + `profil_sekolah.json` (bahan RAG).
Kolom `sumber_data` = `asli` / `dilengkapi` (sintetis) / `diperbaiki`. Hasil dibuat deterministik (seed tetap) oleh `build_dataset.py`.

## Hasil validasi (validate.py): 0 error
Tidak ada sel kosong / "-", semua foreign key valid, tidak ada bentrok jadwal (guru/ruang/kelas), guru hanya mengajar mapel yang dikuasai,
nilai lengkap 6 semester x 13 mapel (RPL 14), kehadiran = hari efektif, kuota PKL tidak terlampaui, 1 penempatan PKL per siswa.

## Yang diperbaiki / dilengkapi
| Kategori | Tabel | Jumlah | Keterangan |
|---|---|---|---|
| normalisasi | siswa | 540 | 5 format JSON disatukan; gender L/P; NIS/NISN string |
| dilengkapi | siswa, nilai, kehadiran, pelanggaran, ekskul | 72 siswa | XII DKV 2 & XII TITL 6 (data siswa tidak ada). Nama baru, pola dari siswa jurusan sama |
| dilengkapi | jadwal | 39 | Jadwal TITL 4, 5, 6 mengikuti pola TITL 1-3 |
| diperbaiki | jadwal | 2 | Bentrok guru B.ING dipindah (lihat `_log_perbaikan_jadwal.csv`) |
| dikeluarkan | jadwal | 32 | XII TKJ 1-2 (tidak ada siswa, di luar 5 jurusan) |
| dilengkapi | kelas | 17 | Wali kelas dari daftar guru (nama wali di JSON asli tidak ada di daftar guru) |
| dilengkapi | PKL | 180 siswa + 6 perusahaan | TAV, DKV 2, TITL 6; perusahaan TAV: nama nyata, alamat/kontak simulasi |
| diperbaiki | PKL | - | Pembimbing sekolah "-" diisi wali kelas; status sesuai tanggal |
| normalisasi | nilai/ekskul | - | Rumus Excel yang belum terhitung (rata-rata, predikat) dihitung ulang / dihitung sistem |
| diperbaiki | profil | 2 | Typo kunci JSON |

## Kamus tabel (21 tabel)
- jurusan(kode PK) · kelas(kode PK, jurusan_kode, wali_kelas_nip) · siswa(nis PK, nisn, kelas_kode)
- guru(nip PK) · guru_mapel(nip, kode_mapel_jadwal) · mapel_jadwal(kode) · mapel_rapor(kode) · pemetaan_mapel(kode_jadwal -> kode_rapor)
- periode_akademik(semester PK: tahun ajaran, KKM, hari efektif)
- nilai(nis, semester, kode_mapel -> mapel_rapor) · kehadiran(nis, semester: sakit/izin/alpha/hadir)
- jenis_pelanggaran(kode) · pelanggaran(nis, kode_pelanggaran, frekuensi, total_poin) — hanya kejadian nyata
- ekstrakurikuler(kode, ketua_nis) · pembina_ekskul · predikat_ekskul · partisipasi_ekskul(nis, semester, kode_ekskul, nilai, predikat)
- jadwal_pelajaran(kelas_kode, hari, jam_mulai..jam_selesai, kode_mapel, nip_guru, ruangan)
- perusahaan_pkl(kode, jurusan_kode, kuota) · sesi_pkl · penempatan_pkl(nis, kode_perusahaan, sesi, pembimbing_sekolah_nip, status)

## Perlu konfirmasi
1. Cakupan 17 kelas (DKV 2 dan TITL 6 sintetis) dan TKJ dikeluarkan.
2. Semester -> tahun ajaran: 1-2 = 2024/25, 3-4 = 2025/26, 5 = 2026/27 (berjalan), 6 = proyeksi.
3. MULOK dipetakan ke Bahasa Sunda; guru untuk Sejarah/PJOK/Seni Budaya/Informatika/PKWU tidak ada di daftar guru.
4. Data pelanggaran bersifat sensitif; atur akses sebelum dipakai di chatbot.
5. Wali kelas pengganti (lihat tabel kelas) — silakan ganti dengan wali sebenarnya.
6. 10 guru yang akan diberi akun teacher.
