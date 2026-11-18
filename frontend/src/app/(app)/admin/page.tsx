'use client';
import { FormEvent, useState } from 'react';
import { api, Row } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { useLoad, Status } from '@/components/useLoad';

type Tab = 'akun' | 'audit' | 'impor';

export default function Admin() {
  const [tab, setTab] = useState<Tab>('akun');
  const [tick, setTick] = useState(0);
  const [info, setInfo] = useState('');
  const [f, setF] = useState({ username: '', nama: '', role: 'teacher', nip: '' });
  const users = useLoad<{ data: Row[] }>(tab === 'akun' ? `/users?t=${tick}` : null);
  const audit = useLoad<{ data: Row[] }>(tab === 'audit' ? '/admin/audit?page_size=100' : null);
  const impor = useLoad<{ data: Row[] }>(tab === 'impor' ? '/admin/impor' : null);
  const cur = tab === 'akun' ? users : tab === 'audit' ? audit : impor;

  async function buat(e: FormEvent) {
    e.preventDefault(); setInfo('');
    try {
      const r = await api('/users', { method: 'POST', body: { ...f, nip: f.nip || null } });
      setInfo(`Akun ${r.username} dibuat. Kata sandi awal (catat sekarang, tidak ditampilkan lagi): ${r.password_awal}`);
      setF({ username: '', nama: '', role: 'teacher', nip: '' }); setTick(tick + 1);
    } catch (err) { setInfo((err as Error).message); }
  }
  async function ubah(id: number, body: object) {
    try {
      const r = await api(`/users/${id}`, { method: 'PATCH', body });
      setInfo(r.password_baru ? `Kata sandi baru (id ${id}): ${r.password_baru}` : 'Tersimpan.'); setTick(tick + 1);
    } catch (err) { setInfo((err as Error).message); }
  }

  return (
    <div className="space-y-3">
      <h1 className="text-lg font-semibold">Admin</h1>
      <div className="flex gap-2">
        {(['akun', 'audit', 'impor'] as Tab[]).map((t) => <button key={t} className={tab === t ? 'btn' : 'btn-ghost'} onClick={() => setTab(t)}>{t === 'akun' ? 'Akun' : t === 'audit' ? 'Audit log' : 'Riwayat impor'}</button>)}
      </div>
      {info && <p className="rounded bg-blue-50 p-2 text-sm text-blue-900 break-all">{info}</p>}
      {tab === 'akun' && (
        <form onSubmit={buat} className="card grid gap-2 sm:grid-cols-5">
          <input className="input" placeholder="username" value={f.username} onChange={(e) => setF({ ...f, username: e.target.value })} required />
          <input className="input" placeholder="nama" value={f.nama} onChange={(e) => setF({ ...f, nama: e.target.value })} required />
          <select className="input" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="teacher">teacher</option><option value="admin">admin</option></select>
          <input className="input" placeholder="NIP (opsional)" value={f.nip} onChange={(e) => setF({ ...f, nip: e.target.value })} />
          <button className="btn">Buat akun</button>
        </form>
      )}
      <Status loading={cur.loading} error={cur.error} />
      <DataTable rows={cur.data?.data ?? []} />
      {tab === 'akun' && users.data && (
        <div className="card space-y-1 text-sm">
          <p className="font-medium">Aksi akun</p>
          {users.data.data.map((u) => (
            <div key={String(u.id)} className="flex flex-wrap items-center gap-2">
              <span className="w-28">{String(u.username)}</span>
              <button className="btn-ghost" onClick={() => ubah(Number(u.id), { aktif: !u.aktif })}>{u.aktif ? 'Nonaktifkan' : 'Aktifkan'}</button>
              <button className="btn-ghost" onClick={() => ubah(Number(u.id), { reset_password: true })}>Reset kata sandi</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
