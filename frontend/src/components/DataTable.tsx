import type { Row } from '@/lib/api';

const label = (k: string) => k.replace(/_/g, ' ');

export default function DataTable({ rows, empty = 'Tidak ada data.' }: { rows: Row[]; empty?: string }) {
  if (!rows.length) return <p className="text-sm text-slate-500">{empty}</p>;
  const cols = Object.keys(rows[0]);
  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-100 text-xs uppercase text-slate-600">
          <tr>{cols.map((c) => <th key={c} className="whitespace-nowrap px-3 py-2">{label(c)}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
              {cols.map((c) => <td key={c} className="whitespace-nowrap px-3 py-1.5">{r[c] === null || r[c] === '' ? '-' : String(r[c])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
