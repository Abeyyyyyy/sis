'use client';
import { useState } from 'react';
import { Row } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { useLoad, Status } from '@/components/useLoad';

export default function Kelas() {
  const [sel, setSel] = useState('');
  const [hari, setHari] = useState('');
  const list = useLoad<{ data: Row[] }>('/kelas');
  const jadwal = useLoad<{ data: Row[] }>(sel ? `/kelas/${sel}/jadwal?hari=${hari}` : null);
  const siswa = useLoad<{ data: Row[] }>(sel ? `/kelas/${sel}/siswa` : null);
  return (
    <div className="space-y-3">
      <h1 className="text-lg font-semibold">Kelas XII</h1>
      <Status loading={list.loading} error={list.error} />
      <DataTable rows={list.data?.data ?? []} />
      <div className="flex flex-wrap gap-2">
        <select className="input max-w-xs" value={sel} onChange={(e) => setSel(e.target.value)}>
          <option value="">Pilih kelas…</option>
          {list.data?.data.map((k) => <option key={String(k.kode)} value={String(k.kode)}>{String(k.nama)}</option>)}
        </select>
        <select className="input max-w-xs" value={hari} onChange={(e) => setHari(e.target.value)}>
          <option value="">Semua hari</option>
          {['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat'].map((h) => <option key={h}>{h}</option>)}
        </select>
      </div>
      {sel && (
        <>
          <h2 className="font-medium">Jadwal</h2><Status loading={jadwal.loading} error={jadwal.error} /><DataTable rows={jadwal.data?.data ?? []} />
          <h2 className="font-medium">Daftar siswa</h2><DataTable rows={siswa.data?.data ?? []} />
        </>
      )}
    </div>
  );
}
