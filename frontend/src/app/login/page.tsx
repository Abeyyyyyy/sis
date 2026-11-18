'use client';
import { FormEvent, useState } from 'react';
import { api, session, User } from '@/lib/api';

export default function Login() {
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const r = await api<{ access_token: string; user: User }>('/auth/login', { method: 'POST', body: { username, password } });
      session.save(r.access_token, r.user);
      window.location.href = r.user.wajib_ganti_password ? '/akun' : '/chat';
    } catch (err) { setError((err as Error).message); } finally { setBusy(false); }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-sm space-y-4">
        <div>
          <h1 className="text-xl font-semibold text-brand-900">School Intelligence System</h1>
          <p className="text-sm text-slate-500">SMKN 4 Bandung · Kelas XII</p>
        </div>
        <input className="input" placeholder="Username" value={username} onChange={(e) => setU(e.target.value)} autoFocus required />
        <input className="input" type="password" placeholder="Kata sandi" value={password} onChange={(e) => setP(e.target.value)} required />
        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
        <button className="btn w-full" disabled={busy}>{busy ? 'Masuk…' : 'Masuk'}</button>
      </form>
    </main>
  );
}
