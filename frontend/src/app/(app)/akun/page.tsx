'use client';
import { FormEvent, useState } from 'react';
import { api, session } from '@/lib/api';

export default function Akun() {
  const [lama, setLama] = useState('');
  const [baru, setBaru] = useState('');
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const wajib = session.user()?.wajib_ganti_password;

  async function submit(e: FormEvent) {
    e.preventDefault(); setMsg(''); setErr('');
    try {
      await api('/auth/ganti-password', { method: 'POST', body: { password_lama: lama, password_baru: baru } });
      const u = session.user(); const t = session.token();
      if (u && t) session.save(t, { ...u, wajib_ganti_password: false });
      setMsg('Kata sandi diganti.'); setLama(''); setBaru('');
      if (wajib) window.location.href = '/chat';
    } catch (e2) { setErr((e2 as Error).message); }
  }
  return (
    <form onSubmit={submit} className="card max-w-sm space-y-3">
      <h1 className="text-lg font-semibold">Ganti kata sandi</h1>
      {wajib && <p className="rounded bg-amber-50 p-2 text-sm text-amber-800">Ini login pertama. Ganti kata sandi dulu sebelum lanjut.</p>}
      <input className="input" type="password" placeholder="Kata sandi lama" value={lama} onChange={(e) => setLama(e.target.value)} required />
      <input className="input" type="password" placeholder="Kata sandi baru (min. 8 karakter)" minLength={8} value={baru} onChange={(e) => setBaru(e.target.value)} required />
      {msg && <p className="text-sm text-green-700">{msg}</p>}
      {err && <p className="text-sm text-red-700">{err}</p>}
      <button className="btn">Simpan</button>
    </form>
  );
}
