'use client';
import { useState } from 'react';
import { useParams } from 'next/navigation';
import { Row } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { useLoad, Status } from '@/components/useLoad';

const TABS = ['Ringkasan', 'Nilai', 'Kehadiran', 'Pelanggaran', 'Ekskul', 'PKL'] as const;
type Tab = (typeof TABS)[number];

export default function ProfilSiswa() {
  const { nis } = useParams<{ nis: string }>();
  const [tab, setTab] = useState<Tab>('Ringkasan');
  const [semester, setSemester] = useState(0);
  const profil = useLoad<{ data: Record<string, any> }>(`/siswa/${nis}`);
  const nilai = useLoad<{ data: Row[]; rata_rata_per_semester: Row[] }>(tab === 'Nilai' ? `/siswa/${nis}/nilai?semester=${semester}` : null);
  const hadir = useLoad<{ data: Row[] }>(tab === 'Kehadiran' ? `/siswa/${nis}/kehadiran` : null);
  const langgar = useLoad<{ data: Row[] }>(tab === 'Pelanggaran' ? `/siswa/${nis}/pelanggaran` : null);
  const p = profil.data?.data;
  return (
    <div className="space-y-3">
      <Status loading={profil.loading} error={profil.error} />
      {p && (
        <>
          <h1 className="text-lg font-semibold">{p.nama} <span className="text-sm font-normal text-slate-500">· {p.kelas ?? p.kelas_kode}</span></h1>
          <div className="flex flex-wrap gap-1">
            {TABS.map((t) => <button key={t} onClick={() => setTab(t)} className={`rounded px-3 py-1.5 text-sm ${tab === t ? 'bg-brand-600 text-white' : 'bg-white border border-slate-300 hover:bg-slate-100'}`}>{t}</button>)}
          </div>
          {tab === 'Ringkasan' && <DataTable rows={[Object.fromEntries(Object.entries(p).filter(([, v]) => typeof v !== 'object')) as Row]} />}
          {tab === 'Nilai' && (
            <div className="space-y-2">
              <select className="input max-w-xs" value={semester} onChange={(e) => setSemester(Number(e.target.value))}>
                <option value={0}>Semua semester</option>
                {[1, 2, 3, 4, 5, 6].map((s) => <option key={s} value={s}>Semester {s}</option>)}
              </select>
              <Status loading={nilai.loading} error={nilai.error} />
              <h2 className="text-sm font-medium">Rata-rata per semester</h2>
              <DataTable rows={nilai.data?.rata_rata_per_semester ?? []} />
              <h2 className="text-sm font-medium">Rincian</h2>
              <DataTable rows={nilai.data?.data ?? []} />
            </div>
          )}
          {tab === 'Kehadiran' && (<><Status loading={hadir.loading} error={hadir.error} /><DataTable rows={hadir.data?.data ?? []} /></>)}
          {tab === 'Pelanggaran' && (
            <>
              <p className="rounded bg-amber-50 p-2 text-sm text-amber-800">Data sensitif. Akses halaman ini dicatat di audit log.</p>
              <Status loading={langgar.loading} error={langgar.error} />
              <DataTable rows={langgar.data?.data ?? []} empty="Tidak ada catatan pelanggaran." />
            </>
          )}
          {tab === 'Ekskul' && <DataTable rows={(p.ekskul as Row[]) ?? []} empty="Tidak mengikuti ekskul." />}
          {tab === 'PKL' && (p.pkl ? <DataTable rows={[p.pkl as Row]} /> : <p className="text-sm text-slate-500">Belum ada penempatan PKL.</p>)}
        </>
      )}
    </div>
  );
}
