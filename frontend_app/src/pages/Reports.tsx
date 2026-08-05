import { useEffect, useState } from "react";
import { FileText, Download, Send, Calendar, BarChart2, TrendingUp, BookOpen } from "lucide-react";
import { C, mono, SectionHeading } from "../app/shared";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

const TEMPLATES = [
  {
    icon: BarChart2, title: "Monthly Department Risk Summary",
    desc: "A comprehensive institutional overview of all student risk levels, subject performance, and intervention statistics for the current month.",
    color: C.navy, lastGenerated: "Jun 30, 2026",
  },
  {
    icon: TrendingUp, title: "Subject-Specific Failure Volatility",
    desc: "Pinpoints which courses have the highest failure rates and tracks volatility trends across the current semester.",
    color: C.high, lastGenerated: "Jul 1, 2026",
  },
  {
    icon: BookOpen, title: "Intervention Effectiveness Audit",
    desc: "Tracks the success rate of Counseling vs. Tutorial sessions, with outcome correlations to student grade improvement.",
    color: C.low, lastGenerated: "Jul 5, 2026",
  },
];

const FORMATS = ["PDF", "XLSX", "CSV"];

export default function Reports() {
  const [startDate, setStartDate] = useState("2026-06-01");
  const [endDate, setEndDate] = useState("2026-06-30");
  const [format, setFormat] = useState("PDF");
  const [email, setEmail] = useState("");
  const [generating, setGenerating] = useState<string | null>(null);
  const [generated, setGenerated] = useState<string[]>([]);
  const [summary, setSummary] = useState<{ run_count: number; average_conflicts: number; average_utilization: number; best_fitness: number } | null>(null);
  const [latestRun, setLatestRun] = useState<{ policy_profile?: { name?: string }; score?: number; assigned_sections?: number; total_sections?: number; recommendation_count?: number } | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/reports/workload-summary`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("Unable to load workload summary")))
      .then((data) => {
        setSummary(data?.summary ?? null);
        setLatestRun(data?.latest_run ?? null);
      })
      .catch(() => {
        setSummary(null);
        setLatestRun(null);
      });
  }, []);

  function generate(title: string) {
    setGenerating(title);
    setTimeout(() => {
      setGenerating(null);
      setGenerated((prev) => [...prev, title]);
    }, 1200);
  }

  async function downloadCsv() {
    const response = await fetch(`${API_BASE_URL}/api/reports/workload-summary.csv`);
    if (!response.ok) {
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "workload-summary.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="px-5 py-4 space-y-4">
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm">
          <p className="text-[24px] font-bold" style={{ ...mono, color: C.navy }}>{summary?.run_count ?? 0}</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">Optimization Runs</p>
        </div>
        <div className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm">
          <p className="text-[24px] font-bold" style={{ ...mono, color: C.blue }}>{summary?.average_conflicts ?? 0}</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">Average Conflicts</p>
        </div>
        <div className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm">
          <p className="text-[24px] font-bold" style={{ ...mono, color: C.low }}>{summary?.average_utilization ?? 0}%</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">Average Utilization</p>
        </div>
        <div className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm">
          <p className="text-[24px] font-bold" style={{ ...mono, color: C.high }}>{summary?.best_fitness ?? 0}</p>
          <p className="text-[10px] text-muted-foreground mt-0.5">Best Fitness</p>
        </div>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>

        {/* Left — Report Templates */}
        <div className="space-y-3">
          <SectionHeading>Report Templates</SectionHeading>
          {TEMPLATES.map(({ icon: Icon, title, desc, color, lastGenerated }) => (
            <div key={title} className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${color}15` }}>
                  <Icon size={18} style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-[13px] font-bold leading-tight mb-1" style={{ color: C.navy }}>{title}</h3>
                  <p className="text-[11px] text-muted-foreground leading-snug mb-3">{desc}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-muted-foreground">Last generated: <span style={mono}>{lastGenerated}</span></span>
                    <button
                      onClick={() => generate(title)}
                      disabled={generating === title}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white transition-all disabled:opacity-60"
                      style={{ background: generating === title ? "#94a3b8" : color }}
                    >
                      {generating === title
                        ? "Generating…"
                        : generated.includes(title)
                          ? <><Download size={12} /> Download</>
                          : <><FileText size={12} /> Generate</>}
                    </button>
                  </div>
                  {generated.includes(title) && (
                    <div className="mt-2 rounded-lg p-2 text-[10px] font-medium" style={{ background: `${C.low}12`, color: C.low }}>
                      ✓ Report generated — ready for download
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Right — Configuration Panel */}
        <div className="bg-white rounded-2xl border border-black/7 p-5 shadow-sm h-fit">
          <SectionHeading>Report Configuration</SectionHeading>
          <div className="space-y-4">

            {/* Date range */}
            <div>
              <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Date Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <div className="relative">
                  <Calendar size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 rounded-xl border border-border text-[12px] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
                <div className="relative">
                  <Calendar size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 rounded-xl border border-border text-[12px] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            </div>

            {/* Format */}
            <div>
              <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                File Format
              </label>
              <div className="flex gap-2">
                {FORMATS.map((f) => (
                  <button
                    key={f}
                    onClick={() => setFormat(f)}
                    className="flex-1 py-2 rounded-xl border text-[12px] font-semibold transition-all"
                    style={format === f
                      ? { background: C.navy, color: "#fff", borderColor: C.navy }
                      : { background: "#fff", color: "#64748b", borderColor: "#e2e8f0" }}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>

            {/* Email distribution */}
            <div>
              <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Email Distribution List
              </label>
              <div className="relative">
                <Send size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="dean@plm.edu.ph, registrar@plm.edu.ph"
                  className="w-full pl-8 pr-3 py-2 rounded-xl border border-border text-[12px] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">Separate multiple addresses with commas</p>
            </div>

            {/* Schedule */}
            <div>
              <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Auto-Schedule
              </label>
              <select className="w-full px-3 py-2 rounded-xl border border-border text-[12px] focus:outline-none bg-white">
                <option>Disabled (Manual only)</option>
                <option>Weekly — every Monday</option>
                <option>Monthly — 1st of each month</option>
                <option>End of semester</option>
              </select>
            </div>

            <div className="pt-2 space-y-2">
              <button className="w-full py-2.5 rounded-xl text-[13px] font-bold text-white transition-colors" style={{ background: C.navy }}>
                Apply Configuration
              </button>
              <button onClick={downloadCsv} className="w-full py-2 rounded-xl border border-border text-[12px] font-semibold text-muted-foreground hover:bg-muted transition-colors flex items-center justify-center gap-1.5">
                <Download size={13} /> Download Workload CSV
              </button>
              {email && (
                <button className="w-full py-2 rounded-xl border border-border text-[12px] font-semibold text-muted-foreground hover:bg-muted transition-colors flex items-center justify-center gap-1.5">
                  <Send size={13} /> Schedule &amp; Send to {email.split(",").length} recipient{email.split(",").length > 1 ? "s" : ""}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-black/7 p-5 shadow-sm">
        <SectionHeading>Latest Workload Run</SectionHeading>
        <div className="grid grid-cols-4 gap-3 text-[12px]">
          <div>
            <p className="text-muted-foreground text-[10px] uppercase tracking-wider">Profile</p>
            <p className="font-semibold" style={{ color: C.slate }}>{latestRun?.policy_profile?.name ?? "No runs yet"}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] uppercase tracking-wider">Score</p>
            <p className="font-semibold" style={{ color: C.slate }}>{latestRun?.score ?? 0}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] uppercase tracking-wider">Sections</p>
            <p className="font-semibold" style={{ color: C.slate }}>{latestRun?.assigned_sections ?? 0}/{latestRun?.total_sections ?? 0}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] uppercase tracking-wider">Recommendations</p>
            <p className="font-semibold" style={{ color: C.slate }}>{latestRun?.recommendation_count ?? 0}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
