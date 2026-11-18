import './globals.css';
import type { ReactNode } from 'react';

export const metadata = { title: 'SIS SMKN 4 Bandung', description: 'School Intelligence System kelas XII' };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (<html lang="id"><body>{children}</body></html>);
}
