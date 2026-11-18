'use client';
import { useEffect } from 'react';
import { session } from '@/lib/api';

export default function Home() {
  useEffect(() => { window.location.replace(session.token() ? '/chat' : '/login'); }, []);
  return null;
}
