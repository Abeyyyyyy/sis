'use client';
import { ReactNode, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { session, User } from '@/lib/api';

const MENU = [
  ['/chat', 'Tanya AI'], ['/siswa', 'Siswa'], ['/kelas', 'Kelas & Jadwal'], ['/pkl', 'PKL'], ['/ekskul', 'Ekskul'],
];

export default function AppLayout({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const path = usePathname();

  useEffect(() => {
    const u = session.user();
    if (!session.token() || !u) { window.location.replace('/login'); return; }
    setUser(u);
    if (u.wajib_ganti_password && path !== '/akun') window.location.replace('/akun');
  }, [path]);

  if (!user) return null;
  const items = user.role === 'admin' ? [...MENU, ['/admin', 'Admin']] : MENU;
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-2 px-4 py-2">
          <span className="mr-4 font-semibold text-brand-900">SIS XII</span>
          <nav className="flex flex-wrap gap-1">
            {items.map(([href, nama]) => (
              <Link key={href} href={href} className={`rounded px-3 py-1.5 text-sm ${path.startsWith(href) ? 'bg-brand-100 text-brand-900' : 'hover:bg-slate-100'}`}>{nama}</Link>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2 text-sm">
            <Link href="/akun" className="text-slate-600 hover:underline">{user.nama} ({user.role})</Link>
            <button className="btn-ghost" onClick={() => { session.clear(); window.location.href = '/login'; }}>Keluar</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4">{children}</main>
    </div>
  );
}
