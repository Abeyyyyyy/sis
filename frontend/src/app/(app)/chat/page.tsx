'use client';
import { FormEvent, useRef, useState, useEffect } from 'react';
import { api, Row } from '@/lib/api';
import DataTable from '@/components/DataTable';

type Msg = { role: 'user' | 'ai'; text: string; tabel?: Row[] | null; sumber?: string[]; sensitif?: boolean; mode?: string };

const AWAL = ['Siapa wali kelas XII TITL 6?', 'Siswa XII RPL 1 yang nilainya di bawah KKM', 'Ranking kelas XII DKV 1 semester 5', 'Jadwal XII TOI 1 hari Senin', 'PKL Aditya Ramadhan di mana?', 'Ekskul apa saja yang ada?'];

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [contoh, setContoh] = useState<string[]>(AWAL);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  async function kirim(pesan: string) {
    if (!pesan.trim() || busy) return;
    setMsgs((m) => [...m, { role: 'user', text: pesan }]); setInput(''); setBusy(true);
    try {
      const r = await api('/chat', { method: 'POST', body: { pesan } });
      setMsgs((m) => [...m, { role: 'ai', text: r.jawaban, tabel: r.tabel, sumber: r.sumber, sensitif: r.sensitif, mode: r.mode }]);
      if (r.contoh?.length) setContoh(r.contoh);
    } catch (e) {
      setMsgs((m) => [...m, { role: 'ai', text: (e as Error).message }]);
    } finally { setBusy(false); }
  }
  const submit = (e: FormEvent) => { e.preventDefault(); kirim(input); };

  return (
    <div className="mx-auto max-w-3xl space-y-3">
      <h1 className="text-lg font-semibold">Tanya data sekolah (kelas XII)</h1>
      <div className="space-y-3">
        {msgs.length === 0 && <p className="text-sm text-slate-500">Tanyakan apa saja tentang siswa, nilai, kehadiran, jadwal, PKL, ekskul, atau profil sekolah.</p>}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'flex justify-end' : ''}>
            <div className={`max-w-full rounded-lg p-3 text-sm ${m.role === 'user' ? 'bg-brand-600 text-white' : 'card'}`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.sensitif && <p className="mt-2 rounded bg-amber-50 p-1.5 text-xs text-amber-800">Data sensitif. Akses ini dicatat di audit log.</p>}
              {m.tabel && m.tabel.length > 0 && <div className="mt-2"><DataTable rows={m.tabel} /></div>}
              {m.sumber && m.sumber.length > 0 && <p className="mt-2 text-xs text-slate-400">Sumber: {m.sumber.join(', ')}{m.mode ? ` · mode ${m.mode}` : ''}</p>}
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-slate-500">Mencari jawaban…</p>}
        <div ref={end} />
      </div>
      <div className="flex flex-wrap gap-2">
        {contoh.slice(0, 6).map((c) => <button key={c} className="btn-ghost text-xs" onClick={() => kirim(c)}>{c}</button>)}
      </div>
      <form onSubmit={submit} className="flex gap-2">
        <input className="input" placeholder="Tulis pertanyaan…" maxLength={500} value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="btn" disabled={busy}>Kirim</button>
      </form>
    </div>
  );
}
