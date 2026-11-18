'use client';
import { Row } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { useLoad, Status } from '@/components/useLoad';

export default function Ekskul() {
  const { data, error, loading } = useLoad<{ data: Row[] }>('/ekskul');
  return (
    <div className="space-y-3">
      <h1 className="text-lg font-semibold">Ekstrakurikuler</h1>
      <Status loading={loading} error={error} />
      <DataTable rows={data?.data ?? []} />
    </div>
  );
}
