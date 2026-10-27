import { useCallback, useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { C, Card, SectionHeading } from "../app/shared";
import { downloadWorkloadSummary, getWorkloadSummary, type WorkloadSummaryRow } from "../services/api";

function errorText(error: unknown) { return error instanceof Error ? error.message : "The report request failed."; }

export default function Reports() {
  const [rows, setRows] = useState<WorkloadSummaryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null); setNotice(null);
    try { setRows(await getWorkloadSummary()); }
    catch (err) { setRows([]); setError(errorText(err)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  async function exportCsv() {
    setExporting(true); setError(null); setNotice(null);
    try {
      const { blob, filename } = await downloadWorkloadSummary();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a"); link.href = url; link.download = filename; link.click(); URL.revokeObjectURL(url);
      setNotice(`Downloaded ${filename}.`);
    } catch (err) { setError(errorText(err)); }
    finally { setExporting(false); }
  }

  return (
    <div className="space-y-5 p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><SectionHeading>Workload Reports</SectionHeading><p className="mt-1 text-xs text-muted-foreground">Faculty workload totals and allocation metrics returned by the API.</p></div><div className="flex gap-2"><button onClick={() => void load()} disabled={loading} className="flex items-center gap-2 rounded-lg border border-border bg-white px-3 py-2 text-xs font-semibold disabled:opacity-50"><RefreshCw size={13} className={loading ? "animate-spin" : ""} />Refresh</button><button onClick={() => void exportCsv()} disabled={loading || exporting || Boolean(error) || rows.length === 0} title={rows.length === 0 ? "No workload rows are available to export." : "Download the backend-generated workload CSV."} className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50" style={{ background: C.teal }}><Download size={13} />{exporting ? "Exporting…" : "Export CSV"}</button></div></div>
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {notice && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</div>}
      <Card className="overflow-hidden">
        {loading ? <p role="status" className="p-8 text-center text-sm text-muted-foreground">Loading report rows…</p> : error && rows.length === 0 ? <p className="p-8 text-center text-sm text-red-700">Workload summary could not be loaded.</p> : rows.length === 0 ? <p className="p-8 text-center text-sm text-muted-foreground">No workload report data is available because there are no faculty records.</p> : <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left"><thead className="bg-slate-50 text-[10px] uppercase tracking-wide text-slate-500"><tr>{["Faculty", "Employment", "Assigned units", "Maximum units", "Utilization", "Sections", "Mean match", "Conflicts"].map((heading) => <th key={heading} className="p-3">{heading}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.faculty_name}-${row.employment_type}-${index}`} className="border-t border-border"><td className="p-3 text-xs font-semibold">{row.faculty_name}</td><td className="p-3 text-xs">{row.employment_type}</td><td className="p-3 text-xs">{row.assigned_units}</td><td className="p-3 text-xs">{row.max_units}</td><td className="p-3 text-xs">{row.max_units ? `${row.utilization_percent.toFixed(1)}%` : "—"}</td><td className="p-3 text-xs">{row.num_sections}</td><td className="p-3 text-xs">{row.num_sections ? `${(row.avg_match_quality * 100).toFixed(1)}%` : "—"}</td><td className="p-3 text-xs">{row.conflicts}</td></tr>)}</tbody></table></div>}
      </Card>
      <p className="text-xs text-muted-foreground">CSV export includes only fields returned by the workload-summary endpoint. Email scheduling, date filters, PDF, and spreadsheet exports are not provided by the current API.</p>
    </div>
  );
}
