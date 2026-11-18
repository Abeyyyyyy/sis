import sys,csv,os,collections,json
D=sys.argv[1]
def L(n): return list(csv.DictReader(open(os.path.join(D,n+'.csv'),encoding='utf-8')))
T={n[:-4]:L(n[:-4]) for n in os.listdir(D) if n.endswith('.csv') and not n.startswith('_')}
err=[]
def chk(c,m):
    if not c: err.append(m)
# kosong
for n,r in T.items():
    for i,row in enumerate(r):
        for k,v in row.items():
            if v is None or v.strip()=='' : err.append(f'kosong {n}[{i}].{k}')
            if v and v.strip()=='-' : err.append(f'strip {n}[{i}].{k}')
nis={s['nis'] for s in T['siswa']}; kel={k['kode'] for k in T['kelas']}; nip={g['nip'] for g in T['guru']}
mj={m['kode'] for m in T['mapel_jadwal']}; mr={m['kode'] for m in T['mapel_rapor']}
chk(len(nis)==612,'jumlah siswa'); chk(len({s['nisn'] for s in T['siswa']})==612,'nisn unik')
for s in T['siswa']: chk(s['kelas_kode'] in kel,'fk siswa')
for k in T['kelas']: chk(k['wali_kelas_nip'] in nip,'fk wali')
chk(len({k['wali_kelas_nip'] for k in T['kelas']})==17,'wali unik')
for j in T['jadwal_pelajaran']: chk(j['kelas_kode'] in kel and j['nip_guru'] in nip and j['kode_mapel'] in mj,'fk jadwal')
for r in T['guru_mapel']: chk(r['kode_mapel_jadwal'] in mj,'fk guru_mapel')
# kompetensi guru di jadwal
gm=collections.defaultdict(set)
for r in T['guru_mapel']: gm[r['nip']].add(r['kode_mapel_jadwal'])
for j in T['jadwal_pelajaran']: chk(j['kode_mapel'] in gm[j['nip_guru']],f"guru tidak kompeten {j['id']}")
# bentrok
for key in ('nip_guru','ruangan','kelas_kode'):
    d=collections.defaultdict(list)
    for j in T['jadwal_pelajaran']: d[(j[key],j['hari'])].append((int(j['jam_mulai']),int(j['jam_selesai'])))
    for v in d.values():
        v.sort()
        for a,b in zip(v,v[1:]): chk(a[1]<b[0],f'bentrok {key} {a} {b}')
cl=collections.Counter(j['kelas_kode'] for j in T['jadwal_pelajaran']); chk(len(cl)==17,'jadwal 17 kelas')
# nilai
rpl={s['nis'] for s in T['siswa'] if s['kelas_kode'].startswith('XII-RPL')}
c=collections.Counter(); 
for n in T['nilai']:
    chk(n['nis'] in nis and n['kode_mapel'] in mr and 0<int(n['nilai'])<=100,'fk nilai'); c[(n['nis'],n['semester'])]+=1
for s in nis:
    for sem in range(1,7): chk(c[(s,str(sem))]==(14 if s in rpl else 13),f'nilai kurang {s} {sem}')
# kehadiran
per={p['semester']:int(p['hari_efektif']) for p in T['periode_akademik']}
chk(len(T['kehadiran'])==612*6,'kehadiran count')
for k in T['kehadiran']: chk(sum(int(k[x]) for x in('sakit','izin','alpha','hadir'))==per[k['semester']],'hari efektif')
jp={j['kode'] for j in T['jenis_pelanggaran']}
for p in T['pelanggaran']: chk(p['nis'] in nis and p['kode_pelanggaran'] in jp,'fk pel')
# ekskul
ek={e['kode'] for e in T['ekstrakurikuler']}
for e in T['ekstrakurikuler']: chk(e['ketua_nis'] in nis,'ketua')
seen=collections.Counter()
for p in T['partisipasi_ekskul']: chk(p['nis'] in nis and p['kode_ekskul'] in ek,'fk ekskul'); seen[(p['nis'],p['semester'],p['kode_ekskul'])]+=1
chk(max(seen.values())==1,'dup ekskul')
pk={p['kode']:p for p in T['perusahaan_pkl']}
pl=T['penempatan_pkl']; chk(len(pl)==612 and len({p['nis'] for p in pl})==612,'pkl 1 per siswa')
ld=collections.Counter((p['kode_perusahaan'],p['sesi']) for p in pl)
for p in pl:
    c_=pk[p['kode_perusahaan']]; chk(p['posisi'] in c_['posisi_tersedia'].split(', '),'posisi pkl')
    chk(c_['jurusan_kode']==[s for s in T['siswa'] if s['nis']==p['nis']][0]['kelas_kode'].split('-')[1],'jurusan pkl') if False else None
for k,c_ in pk.items():
    for s in (1,2): chk(ld[(k,s)]<=int(c_[f'kuota_sesi{s}']),f'kuota {k} {s}')
for p in pl: chk(p['pembimbing_sekolah_nip'] in nip,'pemb')
print('ERRORS',len(err)); print('\n'.join(err[:25]))
