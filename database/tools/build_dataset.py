#!/usr/bin/env python3
"""
Build dataset bersih SIS (kelas XII SMKN 4 Bandung) dari data mentah (zip data_opat).

Pemakaian:  python3 build_dataset.py <folder_data_mentah> <folder_output>

Semua data yang DILENGKAPI (tidak ada di data asli) ditandai kolom `sumber_data`
dan dihasilkan deterministik (seed tetap) sehingga hasilnya selalu sama.
"""
import sys, os, re, json, glob, csv, random, datetime, collections
import openpyxl

RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
rng = random.Random(20261115)
TODAY = datetime.date(2026, 11, 15)

# ---------------------------------------------------------------- konfigurasi
JURUSAN = {  # kode: (nama konsentrasi, program keahlian)
    'RPL':  ('Rekayasa Perangkat Lunak', 'Pengembangan Perangkat Lunak dan Gim (PPLG)'),
    'DKV':  ('Desain Komunikasi Visual', 'Desain Komunikasi Visual'),
    'TITL': ('Teknik Instalasi Tenaga Listrik', 'Teknik Ketenagalistrikan'),
    'TOI':  ('Teknik Otomasi Industri', 'Teknik Ketenagalistrikan'),
    'TAV':  ('Teknik Audio Video', 'Teknik Elektronika'),
}
KELAS_PER_JURUSAN = [('RPL', 3), ('DKV', 2), ('TITL', 6), ('TOI', 3), ('TAV', 3)]
ALL_KELAS = [f'XII {j} {n}' for j, c in KELAS_PER_JURUSAN for n in range(1, c + 1)]
NEW_KELAS = ['XII DKV 2', 'XII TITL 6']          # tidak ada di data asli
TAHUN_AJARAN_XII = '2026/2027'
PERIODE = {  # semester: (tahun ajaran, tipe, status)
    1: ('2024/2025', 'Ganjil', 'selesai'), 2: ('2024/2025', 'Genap', 'selesai'),
    3: ('2025/2026', 'Ganjil', 'selesai'), 4: ('2025/2026', 'Genap', 'selesai'),
    5: ('2026/2027', 'Ganjil', 'berjalan'), 6: ('2026/2027', 'Genap', 'proyeksi'),
}
HARI = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat']
MAXJP = {'Senin': 11, 'Selasa': 11, 'Rabu': 11, 'Kamis': 11, 'Jumat': 6}

def path(*p): return os.path.join(RAW, *p)
def J(f): return json.load(open(path(f), encoding='utf-8'))
def kelas_from_file(f):
    m = re.search(r'XII[ _](\w+)[ _](\d)', f); return f'XII {m.group(1)} {m.group(2)}'
def jur_of(kelas): return kelas.split()[1]
def kode_kelas(kelas): return kelas.replace(' ', '-')
def sgender(v): return 'L' if str(v).strip() in ('L', 'Laki-laki', 'Laki-Laki') else 'P'

LOG = []   # catatan perubahan
def log(kategori, tabel, jumlah, deskripsi): LOG.append((kategori, tabel, jumlah, deskripsi))

# ================================================================ 1. SISWA
siswa = {}      # nis -> dict
wali_asli = {}  # kelas -> nama wali dari file asli (untuk laporan)
for f in sorted(glob.glob(path('daftar_siswa_*.json'))):
    d = json.load(open(f, encoding='utf-8')); kel = kelas_from_file(f)
    rows = d if isinstance(d, list) else d['siswa']
    if isinstance(d, dict):
        meta = d.get('informasi_kelas') or d
        w = meta.get('wali_kelas') or meta.get('waliKelas')
        if w: wali_asli[kel] = w
    for x in rows:
        nis = str(x['nis']).strip()
        siswa[nis] = dict(nis=nis, nisn=str(x['nisn']).strip(), nama=re.sub(r'\s+', ' ', x['nama'].strip()),
                          jenis_kelamin=sgender(x.get('jenis_kelamin') or x.get('jenisKelamin')),
                          no_absen=int(x.get('no_absen') or x.get('no')), kelas=kel,
                          status='aktif', sumber_data='asli')
log('normalisasi', 'siswa', len(siswa), '5 format JSON berbeda disatukan; jenis kelamin disamakan ke L/P; nomor absen int; NIS/NISN string')

# ---- lengkapi kelas yang belum ada (DKV 2, TITL 6)
def build_name_pools():
    first = {'L': [], 'P': []}; mid = []; last = []
    for s in siswa.values():
        t = s['nama'].split()
        first[s['jenis_kelamin']].append(t[0])
        if len(t) > 2: mid += t[1:-1]
        if len(t) > 1: last.append(t[-1])
    return first, mid, last
FIRST, MID, LAST = build_name_pools()
used_names = {s['nama'] for s in siswa.values()}

def new_name(g):
    for _ in range(1000):
        parts = [rng.choice(FIRST[g])]
        if rng.random() < 0.45: parts.append(rng.choice(MID))
        parts.append(rng.choice(LAST))
        if len(set(parts)) != len(parts): continue
        n = ' '.join(parts)
        if n not in used_names: used_names.add(n); return n
    raise RuntimeError('gagal membuat nama unik')

def seq_params(prefix_kelas):
    """ambil pola NIS/NISN dari kelas acuan (kelas terakhir jurusan yang sama)"""
    cls = [s for s in siswa.values() if s['kelas'] == prefix_kelas]
    nis_max = max(int(s['nis']) for s in cls); nisn_max = max(int(s['nisn']) for s in cls)
    return nis_max, nisn_max, len(cls[0]['nis']), len(cls[0]['nisn'])

for kel, (acuan, nl, np_) in {'XII DKV 2': ('XII DKV 1', 18, 18), 'XII TITL 6': ('XII TITL 5', 33, 3)}.items():
    nis_max, nisn_max, ln, lnn = seq_params(acuan)
    names = [(new_name('L'), 'L') for _ in range(nl)] + [(new_name('P'), 'P') for _ in range(np_)]
    names.sort(key=lambda x: x[0])
    for i, (n, g) in enumerate(names, 1):
        nis = str(nis_max + i).zfill(ln); nisn = str(nisn_max + i).zfill(lnn)
        assert nis not in siswa and nisn not in {s['nisn'] for s in siswa.values()}
        siswa[nis] = dict(nis=nis, nisn=nisn, nama=n, jenis_kelamin=g, no_absen=i, kelas=kel,
                          status='aktif', sumber_data='dilengkapi')
log('dilengkapi', 'siswa', 72, 'Kelas XII DKV 2 dan XII TITL 6 belum ada di data siswa: 36 siswa sintetis per kelas (nama baru, NIS/NISN melanjutkan pola kelas acuan)')
by_kelas = collections.defaultdict(list)
for s in siswa.values(): by_kelas[s['kelas']].append(s)
for k in by_kelas: by_kelas[k].sort(key=lambda s: s['no_absen'])
assert sorted(by_kelas) == sorted(ALL_KELAS), (sorted(by_kelas), ALL_KELAS)
assert all(len(v) == 36 for v in by_kelas.values())

# ================================================================ 2. GURU & MAPEL
def norm_gelar(n):
    n = re.sub(r'\s+', ' ', n.strip()); n = re.sub(r',\s*', ', ', n)
    n = n.replace('M. Pd.', 'M.Pd.')
    n = re.sub(r'(,\s*Gr)$', ', Gr.', n).replace('Gr..', 'Gr.')
    n = re.sub(r'M\.M$', 'M.M.', n)
    return n
guru_raw = J('daftar_guru.json')
guru = {g['nip']: dict(nip=g['nip'], nama=norm_gelar(g['nama']), mapel=g['id_mata_pelajaran']) for g in guru_raw}
changed = sum(1 for g in guru_raw if norm_gelar(g['nama']) != g['nama'])
log('normalisasi', 'guru', changed, 'Penulisan gelar dirapikan (spasi, titik, ", Gr" -> ", Gr.")')
mapel_jadwal = {m['id_mata_pelajaran']: m['nama_mata_pelajaran'] for m in J('daftar_mata_pelajaran.json')}

# ================================================================ 3. JADWAL
jam_raw = {x['id_jam_pelajaran']: x for x in J('jam_mata_pelajaran.json')}
kelas_raw = J('kelas.json')
def rng_jam(s):
    p = str(s).split('-'); return int(p[0]), int(p[-1])
slots = []   # dict: id,kelas,hari,a,b,mapel,nip,ruang,sumber
dropped_tkj = 0
for k in kelas_raw:
    if k['nama_kelas'] not in ALL_KELAS:
        dropped_tkj += len(k['id_jam_pelajaran']); continue
    for jid in k['id_jam_pelajaran']:
        x = jam_raw[jid]; a, b = rng_jam(x['jam'])
        slots.append(dict(id=jid, kelas=k['nama_kelas'], hari=x['hari'], a=a, b=b, mapel=x['id_mata_pelajaran'],
                          nip=x['id_guru'], ruang=x['id_ruangan'], sumber='asli'))
log('dikeluarkan', 'jadwal', dropped_tkj, 'Jadwal XII TKJ 1-2 (kelas ini tidak ada di cakupan 5 jurusan dan tidak punya siswa) tidak dimasukkan')

comp = collections.defaultdict(list)
for g in guru.values():
    for m in g['mapel']: comp[m].append(g['nip'])
rooms_all = sorted({s['ruang'] for s in slots})
rooms_by = collections.defaultdict(list)
for s in slots: rooms_by[(jur_of(s['kelas']), s['mapel'])].append(s['ruang'])

busy_t, busy_r, busy_c = (collections.defaultdict(list) for _ in range(3))
def is_free(lst, a, b): return all(b < x or a > y for x, y in lst)
def occupy(s):
    busy_t[(s['nip'], s['hari'])].append((s['a'], s['b']))
    busy_r[(s['ruang'], s['hari'])].append((s['a'], s['b']))
    busy_c[(s['kelas'], s['hari'])].append((s['a'], s['b']))
def release(s):
    for m, key in ((busy_t, (s['nip'], s['hari'])), (busy_r, (s['ruang'], s['hari'])), (busy_c, (s['kelas'], s['hari']))):
        m[key].remove((s['a'], s['b']))

# deteksi bentrok guru pada data asli -> lepas slot kedua agar ditempatkan ulang
def find_conflicts(sl):
    d = collections.defaultdict(list); out = []
    for s in sl: d[(s['nip'], s['hari'])].append(s)
    for v in d.values():
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                if v[i]['a'] <= v[j]['b'] and v[j]['a'] <= v[i]['b']: out.append(v[j])
    return out
to_fix = find_conflicts(slots)
fix_ids = {s['id'] for s in to_fix}
for s in slots:
    if s['id'] not in fix_ids: occupy(s)
slot_log = []

def place(tmpl, teacher_order, mode='teacher_first'):
    """tmpl: dict(kelas,hari,a,b,mapel,ruang). kembalikan slot baru atau None"""
    L = tmpl['b'] - tmpl['a']; cand_times = [(tmpl['hari'], tmpl['a'])]
    others = [(h, a) for h in HARI for a in range(1, MAXJP[h] - L + 1) if (h, a) != (tmpl['hari'], tmpl['a'])]
    rng.shuffle(others)
    others.sort(key=lambda t: (t[0] != tmpl['hari'], abs(t[1] - tmpl['a'])))
    cand_times += others
    jur = jur_of(tmpl['kelas'])
    room_pref = [tmpl['ruang']] + rooms_by[(jur, tmpl['mapel'])] + rooms_all
    def try_one(nip, hari, a):
        b = a + L
        if not is_free(busy_c[(tmpl['kelas'], hari)], a, b): return None
        if not is_free(busy_t[(nip, hari)], a, b): return None
        for r in room_pref:
            if is_free(busy_r[(r, hari)], a, b):
                return dict(id=None, kelas=tmpl['kelas'], hari=hari, a=a, b=b, mapel=tmpl['mapel'], nip=nip, ruang=r)
        return None
    if mode == 'teacher_first':
        for nip in teacher_order:
            for hari, a in cand_times:
                s = try_one(nip, hari, a)
                if s: return s
    else:
        for hari, a in cand_times:
            for nip in teacher_order:
                s = try_one(nip, hari, a)
                if s: return s
    return None

# perbaiki bentrok guru pada data asli
for s in to_fix:
    pool = [s['nip']] + [n for n in comp[s['mapel']] if n != s['nip']]
    new = place(s, pool[1:] + pool[:1], mode='time_first')
    assert new, f'gagal memperbaiki {s}'
    new['id'] = s['id']; new['sumber'] = 'diperbaiki'; occupy(new)
    slots = [x for x in slots if x['id'] != s['id']] + [new]
    slot_log.append((s['id'], s['kelas'], s['mapel'], f"{s['hari']} {s['a']}-{s['b']} {guru[s['nip']]['nama']}",
                     f"{new['hari']} {new['a']}-{new['b']} {guru[new['nip']]['nama']}"))
log('diperbaiki', 'jadwal', len(to_fix), 'Bentrok jadwal guru (guru B.ING mengajar dua kelas di jam yang sama) dipindah ke guru lain / jam lain')

# jadwal untuk kelas yang belum punya (TITL 4-6) -> salin pola TITL 1-3
tmpl_map = {'XII TITL 4': 'XII TITL 1', 'XII TITL 5': 'XII TITL 2', 'XII TITL 6': 'XII TITL 3'}
titl_teachers = collections.defaultdict(collections.Counter)
for s in slots:
    if jur_of(s['kelas']) == 'TITL': titl_teachers[s['mapel']][s['nip']] += 1
next_id = max(int(i[2:]) for i in jam_raw) + 1
new_slots = []
for kel, src in tmpl_map.items():
    tmpls = [s for s in slots if s['kelas'] == src]
    done = None
    for attempt in range(400):
        order = sorted(tmpls, key=lambda t: -(t['b'] - t['a']))
        if attempt:
            rng.shuffle(order)
            if attempt < 200: order.sort(key=lambda t: -(t['b'] - t['a']))
        placed = []; ok = True
        for t in order:
            pref = [n for n, _ in titl_teachers[t['mapel']].most_common()]
            pool = [t['nip']] + [n for n in pref if n != t['nip']] + [n for n in comp[t['mapel']] if n not in pref and n != t['nip']]
            if attempt >= 100: rng.shuffle(pool)
            new = place(dict(kelas=kel, hari=t['hari'], a=t['a'], b=t['b'], mapel=t['mapel'], ruang=t['ruang']), pool)
            if not new: ok = False; break
            new['sumber'] = 'dilengkapi'; occupy(new); placed.append(new)
        if ok: done = placed; break
        for n in placed: release(n)
    assert done, f'gagal menjadwalkan {kel}'
    done.sort(key=lambda s: (HARI.index(s['hari']), s['a']))
    for n in done: n['id'] = f'JP{next_id:04d}'; next_id += 1
    new_slots += done
slots += new_slots
log('dilengkapi', 'jadwal', len(new_slots), 'Jadwal XII TITL 4, 5, 6 dibuat mengikuti pola TITL 1-3 tanpa bentrok guru/ruang/kelas')
# verifikasi bentrok
for key_f, nm in ((lambda s: (s['nip'], s['hari']), 'guru'), (lambda s: (s['ruang'], s['hari']), 'ruang'), (lambda s: (s['kelas'], s['hari']), 'kelas')):
    d = collections.defaultdict(list)
    for s in slots: d[key_f(s)].append(s)
    for v in d.values():
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                assert not (v[i]['a'] <= v[j]['b'] and v[j]['a'] <= v[i]['b']), ('bentrok', nm, v[i], v[j])
slots.sort(key=lambda s: (ALL_KELAS.index(s['kelas']), HARI.index(s['hari']), s['a']))

# ---- wali kelas (dari daftar guru; satu guru satu kelas)
cnt = collections.defaultdict(collections.Counter)
for s in slots:
    cnt[s['kelas']][s['nip']] += 1
wali, used = {}, set()
for kel in sorted(ALL_KELAS, key=lambda k: len(cnt[k])):
    cands = [n for n, _ in cnt[kel].most_common() if n not in used]
    pick = cands[0] if cands else next(n for n in guru if n not in used)
    wali[kel] = pick; used.add(pick)
log('dilengkapi', 'kelas', 17, 'Wali kelas ditetapkan untuk 17 kelas dari daftar guru (guru yang mengajar di kelas tsb); nama wali di JSON asli tidak ada di daftar guru')

# ================================================================ 4. NILAI
UMUM = {'Matematika': 'MAT', 'B. Indonesia': 'B.IND', 'Bahasa Indonesia': 'B.IND', 'B. Inggris': 'B.ING', 'Bahasa Inggris': 'B.ING',
        'B. Sunda': 'B.SUN', 'Bahasa Sunda': 'B.SUN', 'Sejarah': 'SEJ', 'PP (Pendidikan Pancasila)': 'PP', 'Pendidikan Pancasila (PP)': 'PP',
        'PABP (Pendidikan Agama)': 'PABP', 'Pendidikan Agama & Budi Pekerti': 'PABP', 'PJOK': 'PJOK', 'Seni Budaya': 'SBD',
        'Informatika': 'INF', 'PKWU (Prakarya & Kewirausahaan)': 'PKWU'}
def kode_rapor(nama, jur):
    if nama in UMUM: return UMUM[nama]
    m = re.search(r'KK(\d)$', nama.strip())
    if m: return f'{jur}-KK{m.group(1)}'
    raise KeyError(nama)
nilai = {}            # (nis, sem, kode) -> nilai
kkm = {}              # sem -> kkm
for f in sorted(glob.glob(path('Nilai_Siswa_XII_*.xlsx'))):
    wb = openpyxl.load_workbook(f, data_only=True)
    if f.endswith('RPL.xlsx'):
        for ws in wb:
            m = re.match(r'RPL (\d) Sem (\d)', ws.title)
            if not m: continue
            rows = list(ws.iter_rows(values_only=True)); sem = int(m.group(2))
            hdr = rows[2]; names = hdr[5:19]
            k = rows[3][5]; kkm.setdefault(sem, int(k)); assert kkm[sem] == int(k)
            for r in rows[4:]:
                if isinstance(r[0], (int, float)) and r[0] == int(r[0]):
                    for nm, v in zip(names, r[5:19]): nilai[(str(r[1]), sem, kode_rapor(nm, 'RPL'))] = int(v)
        continue
    jur = re.search(r'XII_(\w+)_\d', f).group(1)
    for ws in wb:
        m = re.match(r'Semester (\d)', ws.title)
        if not m: continue
        sem = int(m.group(1)); rows = list(ws.iter_rows(values_only=True))
        k = int(re.search(r'KKM Semester \d: (\d+)', rows[1][0]).group(1)); kkm.setdefault(sem, k); assert kkm[sem] == k
        names = rows[7][5:18]
        for r in rows[8:]:
            if isinstance(r[0], (int, float)) and r[0] == int(r[0]):
                for nm, v in zip(names, r[5:18]): nilai[(str(r[1]), sem, kode_rapor(nm, jur))] = int(v)
assert kkm == {1: 75, 2: 75, 3: 78, 4: 78, 5: 80, 6: 80}, kkm
log('normalisasi', 'nilai', len(nilai), 'Nilai 15 kelas x 6 semester dibaca dari 3 struktur Excel berbeda, nama mapel disamakan ke kode; rata-rata/predikat (rumus Excel) tidak disimpan, dihitung oleh sistem')

# subjek per jurusan -> daftar kode
subj_by_nis = collections.defaultdict(lambda: collections.defaultdict(dict))
for (nis, sem, kode), v in nilai.items(): subj_by_nis[nis][sem][kode] = v
def donors(jur, exclude_kelas):
    return [s for s in siswa.values() if jur_of(s['kelas']) == jur and s['kelas'] not in exclude_kelas and s['sumber_data'] == 'asli']

# donor untuk siswa baru (satu donor tetap per siswa -> pola nilai/kehadiran/pelanggaran/ekskul konsisten)
donor_of = {}
for kel in NEW_KELAS:
    jur = jur_of(kel); pool = donors(jur, NEW_KELAS)
    for s in by_kelas[kel]: donor_of[s['nis']] = rng.choice(pool)['nis']
for kel in NEW_KELAS:
    for s in by_kelas[kel]:
        dn = donor_of[s['nis']]; off = rng.gauss(0, 1.5)
        for sem in range(1, 7):
            for kode, v in subj_by_nis[dn][sem].items():
                if '-KK' in kode: kode_new = f"{jur_of(kel)}-KK{kode[-1]}"
                else: kode_new = kode
                nv = int(round(max(62, min(98, v + off + rng.gauss(0, 2.2)))))
                nilai[(s['nis'], sem, kode_new)] = nv
log('dilengkapi', 'nilai', 72 * 6 * 13, 'Nilai 6 semester untuk 72 siswa baru: pola dari siswa jurusan sama + variasi acak kecil (rentang 62-98 seperti data asli)')

# ================================================================ 5. KEHADIRAN
kehadiran = {}   # (nis, sem) -> (S,I,A,H)
HARI_EFEKTIF = {}
wa = openpyxl.load_workbook(path('daftar_absensi_smkn4.xlsx'), data_only=True)
for ws in wa:
    if not re.match(r'XII \w+ \d$', ws.title): continue
    rows = list(ws.iter_rows(values_only=True))
    hdays = [int(re.search(r'\((\d+) Hr', str(c)).group(1)) for c in rows[3] if c and re.search(r'\((\d+) Hr', str(c))]
    for i, hd in enumerate(hdays, 1):
        HARI_EFEKTIF.setdefault(i, hd); assert HARI_EFEKTIF[i] == hd
    for r in rows[5:]:
        if isinstance(r[0], (int, float)) and r[0] == int(r[0]):
            for sem in range(1, 7):
                S, I, A, H = r[5 + 4 * (sem - 1): 9 + 4 * (sem - 1)]
                assert S + I + A + H == HARI_EFEKTIF[sem]
                kehadiran[(str(r[1]), sem)] = (S, I, A, H)
for kel in NEW_KELAS:
    for s in by_kelas[kel]:
        for sem in range(1, 7):
            S, I, A, _ = kehadiran[(donor_of[s['nis']], sem)]
            kehadiran[(s['nis'], sem)] = (S, I, A, HARI_EFEKTIF[sem] - S - I - A)
log('dilengkapi', 'kehadiran', 72 * 6, 'Kehadiran 6 semester untuk 72 siswa baru (pola dari siswa jurusan sama)')

# ================================================================ 6. PELANGGARAN
wp = openpyxl.load_workbook(path('data_pelanggaran_siswa_smkn4.xlsx'), data_only=True)
jenis = {}  # nama -> (kode, tingkat, poin, sanksi)
for r in list(wp['Referensi Pelanggaran'].iter_rows(values_only=True))[4:]:
    if r[0] and r[0] != 'P-000': jenis[r[1]] = (r[0], r[2], int(r[3]), r[4])
pelanggaran = {}  # nis -> (kode, frek, total, tgl, tindak_lanjut)
for ws in wp:
    if not re.match(r'XII \w+ \d$', ws.title): continue
    for r in list(ws.iter_rows(values_only=True))[4:]:
        if isinstance(r[0], int) and r[5] != 'Tidak Ada Pelanggaran':
            kode, tingkat, poin, _ = jenis[r[5]]
            assert poin == r[7] and tingkat == r[6] and poin * r[8] == r[9]
            pelanggaran[str(r[1])] = (kode, int(r[8]), int(r[9]), str(r[10])[:10], r[11])
for kel in NEW_KELAS:
    for s in by_kelas[kel]:
        dn = donor_of[s['nis']]
        if dn in pelanggaran:
            kode, fr, tot, tgl, ket = pelanggaran[dn]
            d0 = datetime.date.fromisoformat(tgl) + datetime.timedelta(days=rng.randint(-5, 5))
            d0 = min(max(d0, datetime.date(2026, 9, 14)), datetime.date(2026, 11, 12))
            pelanggaran[s['nis']] = (kode, fr, tot, d0.isoformat(), ket)
n_new_pel = sum(1 for k in NEW_KELAS for s in by_kelas[k] if s['nis'] in pelanggaran)
log('dilengkapi', 'pelanggaran', n_new_pel, 'Catatan pelanggaran siswa baru (pola dari siswa jurusan sama, tanggal dalam rentang 14 Sep-12 Nov 2026)')
log('normalisasi', 'pelanggaran', len(pelanggaran) - n_new_pel, 'Baris "Tidak Ada Pelanggaran" (287) tidak dijadikan catatan; tabel hanya berisi kejadian nyata, dihubungkan ke kode jenis pelanggaran')

# ================================================================ 7. EKSKUL
we_files = sorted(glob.glob(path('Data_Nilai_Ekskul', '*.xlsx')))
wb0 = openpyxl.load_workbook(we_files[0], data_only=True)
info_rows = [r for r in wb0['Info Ekskul & Nilai'].iter_rows(values_only=True) if r[1] and str(r[1]).startswith('EKS-')]
assert len(info_rows) == 19
ekskul_nama2kode = {r[2]: r[1] for r in info_rows}
def resolve_ketua(txt):
    m = re.match(r'(.+) \((XII \w+ \d)\)$', txt)
    nm, kel = m.group(1), m.group(2)
    c = [s for s in by_kelas[kel] if s['nama'] == nm]; assert len(c) == 1, txt
    return c[0]['nis']
ekskul = [dict(kode=r[1], nama=r[2], deskripsi=r[3], hari=r[4], waktu=r[5], ketua_nis=resolve_ketua(r[10])) for r in info_rows]
pembina = []
for r in info_rows:
    pembina.append((r[1], 1, r[6], r[7]))
    if r[8] and r[8] != '-': pembina.append((r[1], 2, r[8], r[9]))
predikat_rows = []
for r in wb0['Info Ekskul & Nilai'].iter_rows(values_only=True):
    if r[0] in ('A', 'B', 'C', 'D', 'E') and r[1] is not None and str(r[1]).isdigit():
        predikat_rows.append((r[0], int(r[1]), int(r[2]), r[4], r[5]))
assert len(predikat_rows) == 5
def predikat(v):
    for p, lo, hi, *_ in predikat_rows:
        if lo <= v <= hi: return p
partisipasi = []  # (nis, sem, kode_ekskul, nilai)
for f in we_files:
    wb = openpyxl.load_workbook(f, data_only=True)
    for sem in range(1, 7):
        for r in list(wb[f'Semester {sem}'].iter_rows(values_only=True))[5:]:
            if isinstance(r[0], (int, float)) and r[0] == int(r[0]):
                for ni, vi in ((8, 9), (11, 12), (14, 15)):
                    if r[ni] not in (None, '-'): partisipasi.append((str(r[2]), sem, ekskul_nama2kode[r[ni]], int(r[vi])))
by_don = collections.defaultdict(list)
for p in partisipasi: by_don[p[0]].append(p)
newp = []
for kel in NEW_KELAS:
    for s in by_kelas[kel]:
        off = rng.gauss(0, 1.5)
        for nis, sem, ek, v in by_don.get(donor_of[s['nis']], []):
            newp.append((s['nis'], sem, ek, int(round(max(25, min(98, v + off + rng.gauss(0, 2)))))))
partisipasi += newp
log('dilengkapi', 'partisipasi_ekskul', len(newp), 'Keikutsertaan ekskul siswa baru (pola dari siswa jurusan sama)')
log('normalisasi', 'partisipasi_ekskul', len(partisipasi) - len(newp), 'Baris "Tidak Ikut" dan sel "-" dibuang (tidak ikut = tidak ada baris); predikat dihitung dari kriteria nilai karena rumus Excel belum terhitung; ketua ekskul dikonversi ke NIS')

# ================================================================ 8. PKL
wk = openpyxl.load_workbook(path('Data_PKL_2026-2027.xlsx'), data_only=True)
PREF = {'TITL': 'T', 'RPL': 'R', 'TOI': 'O', 'DKV': 'D', 'TAV': 'A'}
perusahaan = {}
for r in list(wk['Daftar Perusahaan'].iter_rows(values_only=True))[4:]:
    if r[0] and re.match(r'^[A-Z]\d\d$', str(r[0])):
        perusahaan[r[0]] = dict(kode=r[0], nama=r[1], jurusan=[j for j, p in PREF.items() if p == r[0][0]][0], bidang=r[2], alamat=r[3], kota=r[4],
                                kuota1=int(r[5]), kuota2=int(r[6]), posisi=[p.strip() for p in r[8].split(',')], narahubung=r[9], telepon=r[10], sumber_data='asli')
# perusahaan baru untuk TAV (belum ada penempatan TAV di data asli)
TAV_COMP = [
    ('TVRI Jawa Barat', 'Penyiaran Televisi', 'Kota Bandung', ['Teknisi Audio Video', 'Operator Studio dan Penyiaran', 'Teknisi Kamera dan Peralatan Studio']),
    ('Radio Republik Indonesia (RRI) Bandung', 'Penyiaran Radio', 'Kota Bandung', ['Teknisi Audio Video', 'Sound Engineer', 'Operator Studio dan Penyiaran']),
    ('PT INTI (Persero)', 'Telekomunikasi dan Elektronika', 'Kota Bandung', ['Teknisi Elektronika', 'Teknisi Perawatan Perangkat Audio Visual', 'Teknisi Broadcasting']),
    ('PT Len Industri (Persero)', 'Industri Elektronika', 'Kota Bandung', ['Teknisi Elektronika', 'Teknisi Perawatan Perangkat Audio Visual', 'Sound Engineer']),
    ('PT Telkom Indonesia (Persero) Tbk', 'Telekomunikasi dan Teknologi Informasi', 'Kota Bandung', ['Teknisi Broadcasting', 'Teknisi Audio Video', 'Teknisi Elektronika']),
    ('PT Pikiran Rakyat', 'Media Massa dan Penerbitan', 'Kota Bandung', ['Operator Studio dan Penyiaran', 'Sound Engineer', 'Teknisi Kamera dan Peralatan Studio']),
]
PEMB_POOL = ['Hendra Kusuma', 'Sri Wahyuni', 'Rudi Hermawan', 'Yanti Susanti', 'Dedi Kurniadi', 'Nurul Hidayah', 'Teddy Permana',
             'Lia Amalia', 'Wawan Setiawan', 'Euis Komariah', 'Iwan Ridwan', 'Ratna Dewi']
for i, (nm, bd, kota, pos) in enumerate(TAV_COMP, 1):
    kode = f'A{i:02d}'
    perusahaan[kode] = dict(kode=kode, nama=nm, jurusan='TAV', bidang=bd, alamat=f'{kota} (alamat simulasi)', kota=kota, kuota1=0, kuota2=0,
                            posisi=pos, narahubung=PEMB_POOL[i - 1], telepon=f'(022) 20{i}{i:02d}00', sumber_data='dilengkapi')
name2kode = collections.defaultdict(list)
for k, c in perusahaan.items(): name2kode[(c['nama'], c['jurusan'])].append(k)
penempatan = []  # dict
for ws in wk:
    m = re.match(r'XII (\w+) \d$', ws.title)
    if not m: continue
    for r in list(ws.iter_rows(values_only=True))[4:]:
        if isinstance(r[0], (int, float)) and r[0] == int(r[0]):
            k = name2kode[(r[7], m.group(1))][0]
            penempatan.append(dict(nis=str(r[1]), kode=k, posisi=r[10], sesi=int(r[11].split()[1]), pemb=r[13], sumber='asli'))
need = [s for kel in ALL_KELAS for s in by_kelas[kel] if s['nis'] not in {p['nis'] for p in penempatan}]
assert len(need) == 36 * 5, len(need)   # TITL 6, DKV 2, TAV 1-3
load = collections.Counter((p['kode'], p['sesi']) for p in penempatan)
for s in sorted(need, key=lambda s: (ALL_KELAS.index(s['kelas']), s['no_absen'])):
    jur = jur_of(s['kelas']); sesi = 1 if s['no_absen'] % 2 == 1 else 2
    codes = sorted([k for k, c in perusahaan.items() if c['jurusan'] == jur], key=lambda k: (load[(k, sesi)], k))
    k = codes[0]; load[(k, sesi)] += 1
    penempatan.append(dict(nis=s['nis'], kode=k, posisi=rng.choice(perusahaan[k]['posisi']), sesi=sesi, pemb=perusahaan[k]['narahubung'], sumber='dilengkapi'))
for k, c in perusahaan.items():
    c['kuota1'] = max(c['kuota1'], load[(k, 1)]); c['kuota2'] = max(c['kuota2'], load[(k, 2)])
log('dilengkapi', 'penempatan_pkl', len(need), 'Penempatan PKL untuk 180 siswa (TAV 1-3, DKV 2, TITL 6) yang belum ada; sesi mengikuti aturan asli (absen ganjil = Sesi 1, genap = Sesi 2)')
log('dilengkapi', 'perusahaan_pkl', len(TAV_COMP), '6 perusahaan mitra baru untuk jurusan TAV (nama organisasi nyata, alamat/kontak SIMULASI); kuota perusahaan jurusan lain dinaikkan agar cukup untuk kelas tambahan')
log('diperbaiki', 'penempatan_pkl', 216, 'Pembimbing sekolah yang "-" diisi wali kelas; status disesuaikan tanggal (Sesi 1 selesai, Sesi 2 berlangsung); kolom Catatan (kosong semua) dibuang')

# ================================================================ 9. PROFIL SEKOLAH
prof = J('data_opat.json')
def ren(d):
    if isinstance(d, dict):
        return {{'ekstrakulikuler_dan_organisasi': 'ekstrakurikuler_dan_organisasi', 'organisasi_siswas': 'organisasi_siswa'}.get(k, k): ren(v) for k, v in d.items()}
    if isinstance(d, list): return [ren(x) for x in d]
    return d
prof = ren(prof)
log('diperbaiki', 'profil_sekolah', 2, 'Kunci JSON salah ketik diperbaiki: ekstrakulikuler -> ekstrakurikuler, organisasi_siswas -> organisasi_siswa')

# ================================================================ 10. TULIS CSV
def wcsv(name, header, rows):
    rows = list(rows)
    with open(os.path.join(OUT, name + '.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(header); w.writerows(rows)
    return len(rows)
T = collections.OrderedDict()   # nama tabel -> (header, rows)
T['jurusan'] = (['kode', 'nama_konsentrasi', 'program_keahlian'], [(k, v[0], v[1]) for k, v in JURUSAN.items()])
T['kelas'] = (['kode', 'nama', 'jurusan_kode', 'tingkat', 'tahun_ajaran', 'wali_kelas_nip'],
              [(kode_kelas(k), k, jur_of(k), 12, TAHUN_AJARAN_XII, wali[k]) for k in ALL_KELAS])
T['siswa'] = (['nis', 'nisn', 'nama', 'jenis_kelamin', 'no_absen', 'kelas_kode', 'status', 'sumber_data'],
              [(s['nis'], s['nisn'], s['nama'], s['jenis_kelamin'], s['no_absen'], kode_kelas(s['kelas']), s['status'], s['sumber_data'])
               for k in ALL_KELAS for s in by_kelas[k]])
T['guru'] = (['nip', 'nama'], [(g['nip'], g['nama']) for g in guru.values()])
T['guru_mapel'] = (['nip', 'kode_mapel_jadwal'], [(g['nip'], m) for g in guru.values() for m in g['mapel']])
T['mapel_jadwal'] = (['kode', 'nama'], list(mapel_jadwal.items()))
rapor = [('PABP', 'Pendidikan Agama dan Budi Pekerti', 'umum', 'SEMUA'), ('PP', 'Pendidikan Pancasila', 'umum', 'SEMUA'),
         ('B.IND', 'Bahasa Indonesia', 'umum', 'SEMUA'), ('MAT', 'Matematika', 'umum', 'SEMUA'), ('B.ING', 'Bahasa Inggris', 'umum', 'SEMUA'),
         ('SEJ', 'Sejarah', 'umum', 'SEMUA'), ('B.SUN', 'Bahasa Sunda', 'umum', 'SEMUA'), ('PJOK', 'Pendidikan Jasmani, Olahraga, dan Kesehatan', 'umum', 'SEMUA'),
         ('SBD', 'Seni Budaya', 'umum', 'SEMUA'), ('INF', 'Informatika', 'umum', 'SEMUA'),
         ('PKWU', 'Prakarya dan Kewirausahaan', 'umum', 'RPL')]
RPL_KK = {1: 'Pemrograman Web dan Perangkat Bergerak', 2: 'Basis Data dan Pemrograman Berorientasi Objek', 3: 'Proyek Kreatif dan Kewirausahaan (PKK)'}
for j in JURUSAN:
    for n in (1, 2, 3):
        rapor.append((f'{j}-KK{n}', RPL_KK[n] if j == 'RPL' else f'Konsentrasi Keahlian {n} ({j})', 'kejuruan', j))
T['mapel_rapor'] = (['kode', 'nama', 'kelompok', 'berlaku_untuk'], rapor)
T['pemetaan_mapel'] = (['kode_jadwal', 'kode_rapor', 'jenis', 'catatan'], [
    ('PAI', 'PABP', 'padanan', 'Pendidikan Agama Islam dan Budi Pekerti = PABP di rapor'),
    ('PP', 'PP', 'langsung', 'Nama sama'), ('B.IND', 'B.IND', 'langsung', 'Nama sama'), ('MAT', 'MAT', 'langsung', 'Nama sama'), ('B.ING', 'B.ING', 'langsung', 'Nama sama'),
    ('MULOK', 'B.SUN', 'padanan', 'Muatan lokal = Bahasa Sunda (perlu diverifikasi sekolah)'),
    ('KK1', '{JURUSAN}-KK1', 'per_jurusan', 'Ganti {JURUSAN} dengan kode jurusan kelas'),
    ('KK2', '{JURUSAN}-KK2', 'per_jurusan', 'Ganti {JURUSAN} dengan kode jurusan kelas'),
    ('KK3', '{JURUSAN}-KK3', 'per_jurusan', 'Ganti {JURUSAN} dengan kode jurusan kelas')])
T['periode_akademik'] = (['semester', 'tahun_ajaran', 'tipe', 'kkm', 'hari_efektif', 'status'],
                         [(s, PERIODE[s][0], PERIODE[s][1], kkm[s], HARI_EFEKTIF[s], PERIODE[s][2]) for s in range(1, 7)])
T['nilai'] = (['nis', 'semester', 'kode_mapel', 'nilai'], [(k[0], k[1], k[2], v) for k, v in sorted(nilai.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]))])
T['kehadiran'] = (['nis', 'semester', 'sakit', 'izin', 'alpha', 'hadir'],
                  [(n, sem, *kehadiran[(n, sem)][:3], kehadiran[(n, sem)][3]) for n in [s['nis'] for k in ALL_KELAS for s in by_kelas[k]] for sem in range(1, 7)])
T['jenis_pelanggaran'] = (['kode', 'nama', 'tingkat', 'poin', 'sanksi_disarankan'], [(v[0], n, v[1], v[2], v[3]) for n, v in jenis.items()])
nis_order = {s['nis']: i for i, s in enumerate(s for k in ALL_KELAS for s in by_kelas[k])}
T['pelanggaran'] = (['id', 'nis', 'kode_pelanggaran', 'frekuensi', 'total_poin', 'tanggal_terakhir', 'tindak_lanjut'],
                    [(i, n, *pelanggaran[n]) for i, n in enumerate(sorted(pelanggaran, key=lambda n: nis_order[n]), 1)])
T['ekstrakurikuler'] = (['kode', 'nama', 'deskripsi', 'hari', 'waktu', 'ketua_nis'], [(e['kode'], e['nama'], e['deskripsi'], e['hari'], e['waktu'], e['ketua_nis']) for e in ekskul])
T['pembina_ekskul'] = (['kode_ekskul', 'urutan', 'nama', 'biodata'], pembina)
T['predikat_ekskul'] = (['predikat', 'nilai_min', 'nilai_maks', 'keterangan', 'deskripsi'], predikat_rows)
T['partisipasi_ekskul'] = (['nis', 'semester', 'kode_ekskul', 'nilai', 'predikat'],
                           [(n, sem, ek, v, predikat(v)) for n, sem, ek, v in sorted(partisipasi, key=lambda p: (nis_order[p[0]], p[1], p[2]))])
T['jadwal_pelajaran'] = (['id', 'kelas_kode', 'hari', 'jam_mulai', 'jam_selesai', 'kode_mapel', 'nip_guru', 'ruangan', 'sumber_data'],
                         [(s['id'], kode_kelas(s['kelas']), s['hari'], s['a'], s['b'], s['mapel'], s['nip'], s['ruang'], s['sumber']) for s in slots])
T['perusahaan_pkl'] = (['kode', 'nama', 'jurusan_kode', 'bidang_usaha', 'alamat', 'kota', 'kuota_sesi1', 'kuota_sesi2', 'posisi_tersedia', 'narahubung', 'telepon', 'sumber_data'],
                       [(c['kode'], c['nama'], c['jurusan'], c['bidang'], c['alamat'], c['kota'], c['kuota1'], c['kuota2'], ', '.join(c['posisi']), c['narahubung'], c['telepon'], c['sumber_data']) for c in perusahaan.values()])
T['sesi_pkl'] = (['sesi', 'tahun_ajaran', 'tanggal_mulai', 'tanggal_selesai', 'aturan'],
                 [(1, '2026/2027', '2026-07-01', '2026-10-30', 'Nomor absen ganjil'), (2, '2026/2027', '2026-11-02', '2027-02-28', 'Nomor absen genap')])
def status_pkl(sesi): return 'Selesai' if sesi == 1 else 'Sedang berlangsung'
T['penempatan_pkl'] = (['nis', 'kode_perusahaan', 'posisi', 'sesi', 'pembimbing_perusahaan', 'pembimbing_sekolah_nip', 'status', 'sumber_data'],
                       [(p['nis'], p['kode'], p['posisi'], p['sesi'], p['pemb'], wali[siswa[p['nis']]['kelas']], status_pkl(p['sesi']), p['sumber'])
                        for p in sorted(penempatan, key=lambda p: nis_order[p['nis']])])
counts = {}
for name, (h, rows) in T.items(): counts[name] = wcsv(name, h, rows)
json.dump(prof, open(os.path.join(OUT, 'profil_sekolah.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
wcsv('_log_perubahan_dataset', ['kategori', 'tabel', 'jumlah', 'deskripsi'], LOG)
wcsv('_log_perbaikan_jadwal', ['id_jadwal', 'kelas', 'mapel', 'sebelum', 'sesudah'], slot_log)
json.dump(dict(counts=counts, wali_asli=wali_asli, wali={k: guru[v]['nama'] for k, v in wali.items()}), open(os.path.join(OUT, '_build_stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(counts, indent=1))
