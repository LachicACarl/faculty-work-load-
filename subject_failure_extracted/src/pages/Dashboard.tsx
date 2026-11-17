import { useEffect, useState } from "react";
import { Users, BookOpen, AlertTriangle, TrendingUp, Cpu, RefreshCw } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from "recharts";
import { C, mono, StatCard, SectionHeading, Card } from "../app/shared";
import {
  runOptimization,
  getFaculty,
  getSections,
  getWorkloadSummary,
  type OptimizationResponse,
  type FacultyData,
} from "../services/api";

interface WorkloadRow {
  faculty_name: string;
  employment_type: string;
  assigned_units: number;
  max_units: number;
  utilization_percent: number;
  num_sections: number;
  avg_match_quality: number;
  conflicts: number;
}

export default function Dashboard() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<OptimizationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [faculty, setFaculty] = useState<FacultyData[]>([]);
  const [sectionCount, setSectionCount] = useState<number | null>(null);
  const [workload, setWorkload] = useState<WorkloadRow[]>([]);
  const [loading, setLoading] = useState(true);

  async function refreshDashboard() {
    setLoading(true);
    setError(null);
    try {
      const [facultyRows, sectionRows, summaryRows] = await Promise.all([
        getFaculty(),
        getSections(),
        getWorkloadSummary(),
      ]);
      setFaculty(facultyRows);
      setSectionCount(sectionRows.length);
      setWorkload(summaryRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load institutional data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshDashboard();
  }, []);

  async function triggerRun() {
    setRunning(true);
    setError(null);
    try {
      const response = await runOptimization({
        specialization_required: true,
        balance_priority: 0.7,
      });
      if (response.status !== "success") {
        throw new Error("The optimizer did not return a validated feasible allocation.");
      }
      setResult(response);
      await refreshDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization failed.");
    } finally {
      setRunning(false);
    }
  }

  const averageUtilization = workload.length
    ? workload.reduce((total, row) => total + row.utilization_percent, 0) / workload.length
    : 0;
  const utilizationData = workload.map((row) => ({
    faculty: row.faculty_name,
    utilization: Number(row.utilization_percent.toFixed(1)),
  }));

  return (
    <div className="space-y-4 px-5 py-4">
      {error && (
        <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Faculty" value={loading ? "…" : faculty.length} sub="Current faculty records" color={C.teal} icon={<Users size={18} />} />
        <StatCard label="Sections" value={loading ? "…" : sectionCount ?? "—"} sub="Current curriculum records" color={C.sky} icon={<BookOpen size={18} />} />
        <StatCard label="Recorded Conflicts" value={loading ? "…" : workload.reduce((sum, row) => sum + row.conflicts, 0)} sub="From saved allocations" color={C.amber} icon={<AlertTriangle size={18} />} />
        <StatCard label="Average Utilization" value={loading ? "…" : `${averageUtilization.toFixed(1)}%`} sub="Based on saved allocations" color={C.green} icon={<TrendingUp size={18} />} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Card className="p-4">
          <SectionHeading>Faculty Workload Utilization (%)</SectionHeading>
          {loading ? (
            <p className="py-12 text-center text-sm text-muted-foreground">Loading actual workload records…</p>
          ) : utilizationData.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">No workload records are available yet.</p>
          ) : (
            <div style={{ height: Math.max(220, Math.min(520, utilizationData.length * 34)) }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={utilizationData} layout="vertical" margin={{ top: 4, right: 24, left: 20, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, "dataMax"]} unit="%" />
                  <YAxis type="category" dataKey="faculty" width={130} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(value) => [`${value}%`, "Utilization"]} />
                  <Bar dataKey="utilization" fill={C.teal} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        <Card className="flex flex-col p-4">
          <SectionHeading>Optimization Engine</SectionHeading>
          <div className="flex flex-1 flex-col items-center justify-center gap-3 py-5">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl" style={{ background: running ? `${C.teal}18` : `${C.slate}10` }}>
              <Cpu size={28} className={running ? "animate-pulse" : ""} style={{ color: running ? C.teal : C.slate }} />
            </div>
            <p className="text-center text-sm font-semibold" style={{ color: C.slate }}>
              {running ? "Running optimization…" : result ? `Validated run ${result.run_id.slice(0, 8)}` : "Ready to run"}
            </p>
            <p className="text-center text-xs text-muted-foreground">
              {running ? "Generating and validating workload assignments" : "A run is saved only when all hard constraints pass."}
            </p>
            <button
              onClick={triggerRun}
              disabled={running || loading}
              className="flex items-center gap-2 rounded-xl px-5 py-2 text-sm font-bold text-white disabled:opacity-50"
              style={{ background: C.teal }}
            >
              <RefreshCw size={14} className={running ? "animate-spin" : ""} />
              {running ? "Running…" : "Run Optimization"}
            </button>
            <button
              onClick={() => void refreshDashboard()}
              disabled={loading || running}
              className="text-xs font-medium text-slate-600 underline disabled:opacity-50"
            >
              Refresh data
            </button>
          </div>
          {result && (
            <div className="grid grid-cols-2 gap-2 border-t border-border pt-3">
              <div><p className="text-lg font-bold" style={mono}>{result.total_fitness.toFixed(3)}</p><p className="text-xs text-muted-foreground">Fitness score</p></div>
              <div><p className="text-lg font-bold" style={mono}>{result.allocations.length}</p><p className="text-xs text-muted-foreground">Assignments</p></div>
              <div><p className="text-lg font-bold" style={mono}>{result.metrics.ga_generations ?? "—"}</p><p className="text-xs text-muted-foreground">GA generations</p></div>
              <div><p className="text-lg font-bold" style={mono}>{result.metrics.ts_iterations ?? "—"}</p><p className="text-xs text-muted-foreground">Tabu iterations</p></div>
            </div>
          )}
        </Card>
      </div>

      <Card className="p-4">
        <SectionHeading>Current Workload Summary</SectionHeading>
        {loading ? (
          <p className="py-8 text-center text-sm text-muted-foreground">Loading…</p>
        ) : workload.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No saved allocation records are available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead><tr className="border-b text-xs text-muted-foreground"><th className="p-2">Faculty</th><th className="p-2">Type</th><th className="p-2">Units</th><th className="p-2">Utilization</th><th className="p-2">Sections</th><th className="p-2">Match</th></tr></thead>
              <tbody>
                {workload.map((row) => (
                  <tr key={row.faculty_name} className="border-b last:border-0">
                    <td className="p-2 font-medium">{row.faculty_name}</td>
                    <td className="p-2">{row.employment_type}</td>
                    <td className="p-2">{row.assigned_units}/{row.max_units}</td>
                    <td className="p-2">{row.utilization_percent.toFixed(1)}%</td>
                    <td className="p-2">{row.num_sections}</td>
                    <td className="p-2">{(row.avg_match_quality * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <footer className="py-1 text-center text-xs text-muted-foreground">
        Institutional workload data is displayed from the connected database.
      </footer>
    </div>
  );
}
