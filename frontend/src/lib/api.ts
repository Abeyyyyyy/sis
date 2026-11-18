export const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export type User = { id: number; username: string; nama: string; nip: string | null; role: 'admin' | 'teacher'; wajib_ganti_password: boolean };
export type Row = Record<string, string | number | boolean | null>;

const KEY = 'sis_token';
const USER = 'sis_user';

export const session = {
  token: (): string | null => { try { return localStorage.getItem(KEY); } catch { return null; } },
  user: (): User | null => { try { const s = localStorage.getItem(USER); return s ? (JSON.parse(s) as User) : null; } catch { return null; } },
  save: (token: string, user: User) => { try { localStorage.setItem(KEY, token); localStorage.setItem(USER, JSON.stringify(user)); } catch { /* abaikan */ } },
  clear: () => { try { localStorage.removeItem(KEY); localStorage.removeItem(USER); } catch { /* abaikan */ } },
};

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

export async function api<T = any>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = session.token();
  if (token) headers.Authorization = `Bearer ${token}`;
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { method: init.method || 'GET', headers, body: init.body ? JSON.stringify(init.body) : undefined });
  } catch {
    throw new ApiError(0, 'Tidak bisa menghubungi server. Pastikan backend berjalan.');
  }
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token && typeof window !== 'undefined' && !path.startsWith('/auth/login')) {
      session.clear();
      window.location.href = '/login';
    }
    throw new ApiError(res.status, json?.error?.message || `Kesalahan ${res.status}`);
  }
  return json as T;
}
