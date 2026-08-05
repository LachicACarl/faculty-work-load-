import { useState } from "react";
import { Users, BookOpen, AlertTriangle, TrendingUp, CheckCircle2, Clock, Cpu, RefreshCw } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, LineChart, Line,
} from "recharts";
import { C, mono, StatCard, SectionHeading, Card } from "../app/shared";

type LogType = "ok" | "warn" | "info";

type OptimizationMetrics = {
  score: number;
  spec_matches: number;
  schedule_conflicts: number;
  policy_violations: number;
  unassigned_subjects: number;
  utilization_rate: number;
};

type OptimizationResult = {
  allocation: Record<string, string | null>;
  metrics: OptimizationMetrics;
  explainable_recommendations: Array<{
    section_id: string;
    course_code: string;
    assigned_faculty: string;
    specialization_matched: boolean;
    explanation: string;
  }>;
};

type OptimizeApiResponse = {
  status: string;
  policy_profile?: {
    id: string;
    name: string;
  };
  objective_weights?: Record<string, number>;
  data: OptimizationResult;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

const utilizationData = [
  { dept: "IT", fullTime: 88, partTime: 62 },
  { dept: "CS", fullTime: 92, partTime: 58 },
  { dept: "Math", fullTime: 76, partTime: 71 },
  { dept: "Physics", fullTime: 84, partTime: 45 },
  { dept: "Eng", fullTime: 79, partTime: 68 },
];

const RUN_HISTORY_SEED = [
  { run: "Run 1", fitness: 0.61, conflicts: 18 },
  { run: "Run 2", fitness: 0.74, conflicts: 11 },
  { run: "Run 3", fitness: 0.82, conflicts: 6 },
  { run: "Run 4", fitness: 0.87, conflicts: 4 },
  { run: "Run 5", fitness: 0.91, conflicts: 3 },
];

const LOG_SEED: Array<{ time: string; event: string; type: LogType }> = [
  { time: "09:41 AM", event: "Tabu Search completed - 3 conflicts remain", type: "warn" },
  { time: "09:38 AM", event: "Constraint Repair resolved 15 hard violations", type: "ok" },
  { time: "09:35 AM", event: "GA crossover - generation 48 / fitness 0.91", type: "info" },
  { time: "09:30 AM", event: "Initial population generated (120 chromosomes)", type: "info" },
  { time: "09:29 AM", event: "Data ingestion complete - 42 faculty, 87 sections", type: "ok" },
  { time: "09:28 AM", event: "Optimization run triggered by Dean Villanueva", type: "info" },
];

const LOG_COLORS = { ok: C.green, warn: C.amber, info: C.sky };

const TOP_MATCHES_SEED = [
  { faculty: "Dr. Ana Reyes", subject: "Advanced Algorithms", dept: "IT", match: 100, units: 3 },
  { faculty: "Prof. Luis Dela Cruz", subject: "Machine Learning", dept: "CS", match: 95, units: 3 },
  { faculty: "Ms. Clara Santos", subject: "Calculus III", dept: "Math", match: 92, units: 3 },
  { faculty: "Dr. Jose Bautista", subject: "Quantum Mechanics", dept: "Physics", match: 88, units: 3 },
  { faculty: "Prof. Maria Torres", subject: "Software Engineering", dept: "IT", match: 86, units: 3 },
];

function currentTimeLabel() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Dashboard() {
  const [running, setRunning] = useState(false);
  const [ran, setRan] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [lastRunLabel, setLastRunLabel] = useState("Not yet run");
  const [runHistory, setRunHistory] = useState(RUN_HISTORY_SEED);
  const [logEntries, setLogEntries] = useState(LOG_SEED);
  const [topMatches, setTopMatches] = useState(TOP_MATCHES_SEED);
  const [optimizationMetrics, setOptimizationMetrics] = useState({
    conflicts: 3,
    utilizationRate: 78,
    assignedSections: 78,
    totalSections: 87,
    bestFitness: 0.91,
  });

  function appendLog(event: string, type: LogType) {
    setLogEntries((prev) => ([
      { time: currentTimeLabel(), event, type },
      ...prev,
    ].slice(0, 8)));
  }

  async function triggerRun() {
    setRunning(true);
    setApiError(null);
    appendLog("Optimization run triggered by dashboard user", "info");

    try {
      const institutionalResponse = await fetch(`${API_BASE_URL}/api/institutional/snapshot`);

      if (!institutionalResponse.ok) {
        throw new Error("Unable to load faculty/curriculum inputs");
      }

      const institutional = await institutionalResponse.json();
      const faculty = Array.isArray(institutional?.faculty) ? institutional.faculty : [];
      const curriculum = institutional?.curriculum ?? {};
      const sections = Array.isArray(curriculum?.sections) ? curriculum.sections : [];

      if (!Array.isArray(faculty) || faculty.length === 0 || sections.length === 0) {
        throw new Error("Optimization requires non-empty faculty and section data");
      }

      appendLog(`Data loaded - ${faculty.length} faculty, ${sections.length} sections`, "ok");

      const optimizeResponse = await fetch(`${API_BASE_URL}/api/workload/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          faculty,
          sections,
          policy_profile: {
            id: "balanced",
            name: "Balanced Baseline",
            full_time_max_units: 21,
            part_time_max_units: 12,
            allowable_overload: 3,
            specialization_required: true,
            consecutive_limit: 2,
            balance_priority: 70,
            utilization_target: 80,
          },
          objective_weights: {
            spec_match: 12,
            utilization: 5,
            conflict: 50,
            policy_violation: 42,
            unassigned: 30,
          },
        }),
      });

      if (!optimizeResponse.ok) {
        const failed = await optimizeResponse.json().catch(() => ({ detail: "optimization request failed" }));
        throw new Error(failed.detail ?? "optimization request failed");
      }

      const optimizePayload = await optimizeResponse.json() as OptimizeApiResponse;
      const result = optimizePayload.data;

      if (!result?.metrics) {
        throw new Error("Optimization response missing metrics");
      }

      const metrics = result.metrics;
      const assignedSections = Object.values(result.allocation ?? {}).filter(Boolean).length;
      const totalSections = sections.length;
      const bestFitness = Number(Math.min(0.99, Math.max(0.5, (metrics.spec_matches + 1) / (totalSections + 1))).toFixed(2));

      setOptimizationMetrics({
        conflicts: metrics.schedule_conflicts,
        utilizationRate: metrics.utilization_rate,
        assignedSections,
        totalSections,
        bestFitness,
      });

      setRunHistory((prev) => {
        const nextRun = `Run ${prev.length + 1}`;
        return [...prev.slice(-4), { run: nextRun, fitness: bestFitness, conflicts: metrics.schedule_conflicts }];
      });

      const mappedMatches = (result.explainable_recommendations ?? []).slice(0, 5).map((item, index) => ({
        faculty: item.assigned_faculty,
        subject: item.course_code,
        dept: "GS",
        match: item.specialization_matched ? 100 : 74,
        units: 3,
        order: index,
      }));

      if (mappedMatches.length > 0) {
        setTopMatches(mappedMatches);
      }

      appendLog(`Tabu Search completed - ${metrics.schedule_conflicts} conflicts remain`, metrics.schedule_conflicts > 0 ? "warn" : "ok");
      appendLog(`Constraint repair finalized assignments - ${assignedSections}/${totalSections} sections allocated`, "ok");
      setLastRunLabel(`Last run: ${currentTimeLabel()}`);
      setRan(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown optimization error";
      setApiError(message);
      appendLog(`Optimization failed - ${message}`, "warn");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="px-5 py-4 space-y-4">
      {/* Stat strip */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Total Faculty" value={42} sub="Full-time & Part-time" color={C.teal} icon={<Users size={18} />} />
        <StatCard label="Sections to Fill" value={optimizationMetrics.totalSections} sub="Current semester" color={C.sky} icon={<BookOpen size={18} />} />
        <StatCard label="Conflicts Detected" value={running ? "..." : optimizationMetrics.conflicts} sub="Hard constraint violations" color={C.amber} icon={<AlertTriangle size={18} />} />
        <StatCard label="Avg. Utilization" value={running ? "..." : `${optimizationMetrics.utilizationRate}%`} sub="Across all departments" color={C.green} icon={<TrendingUp size={18} />} />
      </div>

      {apiError && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[12px] text-red-700">
          {apiError}
        </div>
      )}

      {/* Middle row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1.4fr 1fr" }}>

        {/* Utilization by dept */}
        <Card className="p-4">
          <SectionHeading>Faculty Utilization by Department (%)</SectionHeading>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={utilizationData} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" vertical={false} />
                <XAxis dataKey="dept" tick={{ fontSize: 10, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} domain={[0, 100]} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} formatter={(v) => [`${v}%`]} />
                <Bar dataKey="fullTime" fill={C.teal} name="Full-Time" radius={[3, 3, 0, 0]} />
                <Bar dataKey="partTime" fill={C.sky} name="Part-Time" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-2">
            {[[C.teal, "Full-Time"], [C.sky, "Part-Time"]].map(([c, l]) => (
              <div key={l as string} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm" style={{ background: c as string }} />
                <span className="text-[10px] text-muted-foreground">{l}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Algorithm convergence */}
        <Card className="p-4">
          <SectionHeading>Algorithm Convergence (Fitness Score)</SectionHeading>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={runHistory} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" />
                <XAxis dataKey="run" tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} domain={[0.5, 1]} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                <Line type="monotone" dataKey="fitness" stroke={C.teal} strokeWidth={2.5} dot={{ r: 4, fill: C.teal }} name="Fitness" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Bottom row */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>

        {/* Run control */}
        <Card className="p-4 flex flex-col">
          <SectionHeading>Optimization Engine</SectionHeading>
          <div className="flex-1 flex flex-col items-center justify-center py-4 gap-3">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center" style={{ background: running ? `${C.teal}18` : `${C.slate}10` }}>
              <Cpu size={28} className={running ? "animate-pulse" : ""} style={{ color: running ? C.teal : C.slate }} />
            </div>
            <div className="text-center">
              <p className="text-[13px] font-semibold" style={{ color: C.slate }}>
                {running ? "Running optimization..." : ran ? lastRunLabel : "Ready to run"}
              </p>
              <p className="text-[10.5px] text-muted-foreground mt-0.5">
                {running ? "GA + Tabu Search in progress" : "Modified Hybrid GA + Tabu Search"}
              </p>
            </div>
            {running && (
              <div className="w-full h-1.5 rounded-full bg-[#e2e8f0] overflow-hidden">
                <div className="h-full rounded-full animate-pulse" style={{ width: "70%", background: C.teal }} />
              </div>
            )}
            <button
              onClick={triggerRun}
              disabled={running}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-[13px] font-bold text-white transition-all disabled:opacity-50"
              style={{ background: C.teal }}
            >
              <RefreshCw size={14} className={running ? "animate-spin" : ""} />
              {running ? "Running..." : "Run Optimization"}
            </button>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-border">
            {[[String(runHistory.length), "Runs"], ["20", "Tabu Iterations"], [optimizationMetrics.bestFitness.toFixed(2), "Best Fitness"]].map(([v, l]) => (
              <div key={l} className="text-center">
                <p className="text-[14px] font-bold" style={{ ...mono, color: C.slate }}>{v}</p>
                <p className="text-[9px] text-muted-foreground">{l}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Optimization log */}
        <Card className="p-4">
          <SectionHeading>Latest Run Log</SectionHeading>
          <div className="space-y-2.5">
            {logEntries.map((e, i) => (
              <div key={i} className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: LOG_COLORS[e.type as keyof typeof LOG_COLORS] }} />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] leading-snug" style={{ color: C.slate }}>{e.event}</p>
                  <p className="text-[9px] text-muted-foreground mt-0.5" style={mono}>{e.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top specialty matches */}
        <Card className="p-4">
          <SectionHeading>Top Specialization Matches</SectionHeading>
          <div className="space-y-2.5">
            {topMatches.map((m, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <div className="w-6 h-6 rounded-lg flex-shrink-0 flex items-center justify-center text-white text-[9px] font-bold" style={{ background: C.teal }}>
                  {m.faculty.split(" ").pop()![0]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11.5px] font-semibold leading-tight truncate" style={{ color: C.slate }}>{m.faculty}</p>
                  <p className="text-[10px] text-muted-foreground truncate">{m.subject}</p>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <div className="w-12 h-1 rounded-full bg-[#e2e8f0] overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${m.match}%`, background: m.match >= 90 ? C.green : m.match >= 80 ? C.teal : C.amber }} />
                  </div>
                  <span className="text-[10px] font-bold" style={{ ...mono, color: m.match >= 90 ? C.green : C.teal }}>{m.match}%</span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 size={13} style={{ color: C.green }} />
              <span className="text-[10.5px] text-muted-foreground">{optimizationMetrics.assignedSections} of {optimizationMetrics.totalSections} sections allocated</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock size={12} style={{ color: C.amber }} />
              <span className="text-[10px] text-muted-foreground">{Math.max(0, optimizationMetrics.totalSections - optimizationMetrics.assignedSections)} pending</span>
            </div>
          </div>
        </Card>
      </div>

      <footer className="text-center text-[10px] text-muted-foreground py-1">
        © 2026 PLM Graduate School – Department of Information Technology. All rights reserved.
      </footer>
    </div>
  );
}
