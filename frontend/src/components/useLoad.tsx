'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export function useLoad<T = any>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(!!path);
  useEffect(() => {
    if (!path) return;
    let alive = true;
    setLoading(true); setError('');
    api<T>(path).then((d) => alive && setData(d)).catch((e) => alive && setError(e.message)).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [path]);
  return { data, error, loading };
}

export function Status({ loading, error }: { loading: boolean; error: string }) {
  if (loading) return <p className="text-sm text-slate-500">Memuat…</p>;
  if (error) return <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>;
  return null;
}
