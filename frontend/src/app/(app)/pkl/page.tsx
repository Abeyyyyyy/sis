'use client';
import { useState } from 'react';
import { Row } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { useLoad, Status } from '@/components/useLoad';

export default function Pkl() {
  const [kelas, setKelas] = useState('');
  const [tab, setTab] = useState<'penempatan' | 'perusahaan'>('penempatan');
  const kl = useLoad<{ data: Row[] }>('/kelas');
  const pen = useLoad<{ data: Row[] }>(tab === 'penempatan' ? `/pkl/penempatan?kelas=${kelas}` : null);
  const per = useLoad<{ data: Row[] }>(tab === 'perusahaan' ? '/pkl/perusahaan' : null);
  const cur = tab === 'penempatan' ? pen : per;
  return (
    <div className="space-y-3">
      <h1 className="text-lg font-semibold">PKL</h1>
      <div className="flex flex-wrap gap-2">
        <button className={tab === 'penempatan' ? 'btn' : 'btn-ghost'} onClick={() => setTab('penempatan')}>Penempatan</button>
        <button className={tab === 'perusahaan' ? 'btn' : 'btn-ghost'} onClick={() => setTab('perusahaan')}>Perusahaan</button>
        {tab === 'penempatan' && (
          <select className="input max-w-xs" value={kelas} onChange={(e) => setKelas(e.target.value)}>
            <option value="">Semua kelas</option>
            {kl.data?.data.map((k) => <option key={String(k.kode)} value={String(k.kode)}>{String(k.nama)}</option>)}
          </select>
        )}
      </div>
      <Status loading={cur.loading} error={cur.error} />
      <DataTable rows={cur.data?.data ?? []} />
    </div>
  );
}
