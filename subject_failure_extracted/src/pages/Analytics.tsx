import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { C, Card, SectionHeading } from "../app/shared";
import { getKPIHistory, type KPIHistory } from "../services/api";

function errorText(error: unknown) { return error instanceof Error ? error.message : "The analytics request failed."; }

export default function Analytics() {
  const [data, setData] = useState<KPIHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await getKPIHistory()); }
    catch (err) { setError(errorText(err)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const summary = data?.metric_summary;
  const contractVerified = summary?.data_source === "current_database_aggregates";
  const hasRecords = Boolean(summary && summary.faculty_count + summary.allocation_count > 0);
  const cards = summary && contractVerified ? [
    ["Faculty records", String(summary.faculty_count)],
    ["Current allocations", String(summary.allocation_count)],
    ["Current mean utilization", summary.faculty_count ? `${summary.avg_utilization.toFixed(1)}%` : "—"],
    ["Current conflicts", String(summary.total_conflicts)],
  ] : [];

  return (
    <div className="space-y-5 p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><SectionHeading>Workload Analytics</SectionHeading><p className="mt-1 text-xs text-muted-foreground">Current database aggregates only. No historical observations are available from this API.</p></div><button onClick={() => void load()} disabled={loading} className="flex items-center gap-2 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold disabled:opacity-50"><RefreshCw size={13} className={loading ? "animate-spin" : ""} />Refresh</button></div>
      {loading && <p role="status" className="text-sm text-muted-foreground">Loading analytics…</p>}
      {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">Analytics could not be loaded: {error}</p>}
      {!loading && !error && !contractVerified && <p role="alert" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">The API response does not identify the verified current-aggregate contract. Metrics are withheld until the backend is updated.</p>}
      {!loading && !error && contractVerified && <>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value]) => <Card key={label} className="p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-2xl font-bold" style={{ color: C.slate }}>{value}</p></Card>)}</div>
        {!hasRecords && <Card className="p-6 text-center"><p className="text-sm font-semibold text-slate-700">No workload observations yet.</p><p className="mt-1 text-xs text-muted-foreground">Analytics will appear when faculty and allocation records are available.</p></Card>}
        {hasRecords && <Card className="p-5"><SectionHeading>Historical trends</SectionHeading><p className="mt-2 text-sm text-muted-foreground">No historical observations are stored by the current API, so trend charts are unavailable. Current values above are calculated from the present database records.</p></Card>}
      </>}
    </div>
  );
}
