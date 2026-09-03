import { useState } from "react";
import { Search, Check, X, Info, Filter, Download, ChevronRight } from "lucide-react";
import { C, mono, MatchBadge, StatusBadge, MatchLevel, ApprovalStatus, SectionHeading, Card } from "../app/shared";
import { updateAllocationStatus, downloadWorkloadSummary } from "../services/api";

interface Allocation {
  id: string; faculty: string; subject: string; code: string;
  section: string; dept: string; timeSlot: string; day: string;
  units: number; matchPct: number; matchLevel: MatchLevel;
  status: ApprovalStatus; reason: string;
}

const ALLOCATIONS: Allocation[] = [
  { id: "ALG-001", faculty: "Dr. Ana Reyes", subject: "Advanced Algorithms", code: "CS 501", section: "A", dept: "IT", timeSlot: "7:00–8:30", day: "Mon/Wed", units: 3, matchPct: 100, matchLevel: "Exact", status: "Approved", reason: "100% specialization match (Algorithms) and declared availability on Mon/Wed 7:00–8:30 AM." },
  { id: "ALG-002", faculty: "Prof. Luis Dela Cruz", subject: "Machine Learning", code: "CS 601", section: "A", dept: "CS", timeSlot: "8:30–10:00", day: "Tue/Thu", units: 3, matchPct: 95, matchLevel: "Exact", status: "Approved", reason: "Primary specialization (Machine Learning) matched. Available Tue/Thu 8:30–10:00 AM." },
  { id: "ALG-003", faculty: "Ms. Clara Santos", subject: "Calculus III", code: "MATH 301", section: "A", dept: "Math", timeSlot: "1:00–2:30", day: "Mon/Wed", units: 3, matchPct: 92, matchLevel: "Exact", status: "Pending", reason: "Specialization match (Calculus). Utilization at maximum (21/21 units). Overload not applied." },
  { id: "ALG-004", faculty: "Dr. Jose Bautista", subject: "Quantum Mechanics", code: "PHYS 601", section: "A", dept: "Physics", timeSlot: "7:00–8:30", day: "Tue/Thu", units: 3, matchPct: 88, matchLevel: "Exact", status: "Pending", reason: "Primary specialization matched. Schedule aligned with Tue/Thu availability." },
  { id: "ALG-005", faculty: "Prof. Maria Torres", subject: "Software Engineering", code: "IT 401", section: "B", dept: "IT", timeSlot: "4:00–5:30", day: "Mon/Wed", units: 3, matchPct: 85, matchLevel: "Exact", status: "Approved", reason: "Specialization match (Software Engineering). Part-time slot 4:00–5:30 PM used efficiently." },
  { id: "ALG-006", faculty: "Engr. Paolo Ramos", subject: "Network Security", code: "IT 502", section: "A", dept: "IT", timeSlot: "4:00–5:30", day: "Tue/Thu", units: 3, matchPct: 78, matchLevel: "Partial", status: "Pending", reason: "Partial match: faculty specializes in Networks & Cybersecurity; course includes Cloud Security module outside core area." },
  { id: "ALG-007", faculty: "Dr. Sofia Mendoza", subject: "Computer Vision", code: "CS 701", section: "A", dept: "CS", timeSlot: "8:30–10:00", day: "Mon", units: 3, matchPct: 100, matchLevel: "Exact", status: "Approved", reason: "Exact match (Computer Vision). Only Mon availability overlaps; section moved to single-day format." },
  { id: "ALG-008", faculty: "Prof. Carlos Lim", subject: "Discrete Mathematics", code: "MATH 201", section: "A", dept: "Math", timeSlot: "7:00–8:30", day: "Wed/Fri", units: 3, matchPct: 96, matchLevel: "Exact", status: "Pending", reason: "Specialization match (Discrete Mathematics). Available Wed/Fri 7:00–8:30 AM confirmed." },
  { id: "ALG-009", faculty: "Prof. Luis Dela Cruz", subject: "Data Mining Fundamentals", code: "CS 502", section: "B", dept: "CS", timeSlot: "1:00–2:30", day: "Thu", units: 3, matchPct: 90, matchLevel: "Exact", status: "Pending", reason: "Secondary specialization match (Data Mining). Thu 1:00–2:30 PM slot is declared available." },
  { id: "ALG-010", faculty: "Dr. Ana Reyes", subject: "Automata Theory", code: "CS 401", section: "A", dept: "IT", timeSlot: "10:00–11:30", day: "Mon/Wed", units: 3, matchPct: 58, matchLevel: "Partial", status: "Flagged", reason: "Partial match only: Theory of Computation is adjacent to Automata Theory but not an exact specialization. Manual review required. Faculty already at 18/21 units." },
  { id: "ALG-011", faculty: "Prof. Maria Torres", subject: "Embedded Systems", code: "IT 301", section: "A", dept: "IT", timeSlot: "4:00–5:30", day: "Fri", units: 3, matchPct: 32, matchLevel: "Unmatched", status: "Flagged", reason: "No specialization match. Assigned due to no available faculty with embedded systems expertise. Constraint repair fallback — recommend hiring review." },
];

const DEPT_OPTS = ["All", "IT", "CS", "Math", "Physics"];
const STATUS_OPTS: Array<"All" | ApprovalStatus> = ["All", "Pending", "Approved", "Flagged"];

export default function AllocationReview() {
  const [search, setSearch] = useState("");
  const [deptF, setDeptF] = useState("All");
  const [statusF, setStatusF] = useState<"All" | ApprovalStatus>("All");
  const [detail, setDetail] = useState<Allocation | null>(null);
  const [allocs, setAllocs] = useState<Allocation[]>(ALLOCATIONS);
  const [isUpdating, setIsUpdating] = useState<string | null>(null);

  async function approve(id: string) {
    setIsUpdating(id);
    try {
      // Extract numeric ID from the string ID (e.g., "ALG-001" -> 1)
      const numId = parseInt(id.split("-")[1]) || 1;
      await updateAllocationStatus(numId, "approved");
      setAllocs((a) => a.map((x) => x.id === id ? { ...x, status: "Approved" } : x));
      if (detail?.id === id) setDetail((d) => d ? { ...d, status: "Approved" } : d);
    } catch (err) {
      console.error("Failed to approve:", err);
    } finally {
      setIsUpdating(null);
    }
  }

  async function flag(id: string) {
    setIsUpdating(id);
    try {
      const numId = parseInt(id.split("-")[1]) || 1;
      await updateAllocationStatus(numId, "flagged");
      setAllocs((a) => a.map((x) => x.id === id ? { ...x, status: "Flagged" } : x));
      if (detail?.id === id) setDetail((d) => d ? { ...d, status: "Flagged" } : d);
    } catch (err) {
      console.error("Failed to flag:", err);
    } finally {
      setIsUpdating(null);
    }
  }

  async function handleExport() {
    try {
      const blob = await downloadWorkloadSummary();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "workload-summary.csv";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    }
  }

  const filtered = allocs.filter((a) => {
    const q = search.toLowerCase();
    return (
      (!q || a.faculty.toLowerCase().includes(q) || a.subject.toLowerCase().includes(q) || a.code.toLowerCase().includes(q)) &&
      (deptF === "All" || a.dept === deptF) &&
      (statusF === "All" || a.status === statusF)
    );
  });

  const pending = allocs.filter((a) => a.status === "Pending").length;
  const approved = allocs.filter((a) => a.status === "Approved").length;
  const flagged = allocs.filter((a) => a.status === "Flagged").length;

  return (
    <div className="px-5 py-4 flex flex-col gap-4 h-full">
      {/* Summary strip */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total Allocations", value: allocs.length, color: C.slate },
          { label: "Approved", value: approved, color: C.green },
          { label: "Pending Review", value: pending, color: C.amber },
          { label: "Flagged", value: flagged, color: C.red },
        ].map(({ label, value, color }) => (
          <Card key={label} className="p-3 flex items-center gap-3">
            <span className="text-[24px] font-bold" style={{ ...mono, color }}>{value}</span>
            <span className="text-[11px] text-muted-foreground font-medium">{label}</span>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search faculty, subject, or course code…"
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-border bg-white text-[12.5px] focus:outline-none focus:ring-2 focus:ring-teal-500/20" />
        </div>
        <div className="flex gap-1.5">
          {DEPT_OPTS.map((d) => (
            <button key={d} onClick={() => setDeptF(d)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
              style={deptF === d ? { background: C.slate, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}>
              {d}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          {STATUS_OPTS.map((s) => (
            <button key={s} onClick={() => setStatusF(s)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
              style={statusF === s ? { background: C.teal, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}>
              {s}
            </button>
          ))}
        </div>
        <button 
          onClick={handleExport}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border bg-white text-[12px] font-medium hover:bg-muted transition-colors ml-auto">
          <Download size={13} /> Export
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-black/7 shadow-sm overflow-hidden flex-1 overflow-y-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-white z-10">
            <tr className="border-b border-border">
              {["ID", "Faculty", "Subject / Code", "Dept", "Schedule", "Units", "Match", "Status", "Actions"].map((h) => (
                <th key={h} className="text-left px-3 py-3 text-[9.5px] font-bold uppercase tracking-wider text-muted-foreground whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((a, i) => (
              <tr key={a.id} className={`border-b border-border/50 hover:bg-[#f7fafa] transition-colors ${i % 2 === 0 ? "" : "bg-[#fafbfd]"}`}>
                <td className="px-3 py-2.5 text-[10px] text-muted-foreground" style={mono}>{a.id}</td>
                <td className="px-3 py-2.5 text-[12px] font-semibold whitespace-nowrap" style={{ color: C.slate }}>{a.faculty}</td>
                <td className="px-3 py-2.5">
                  <p className="text-[12px] font-medium" style={{ color: C.slate }}>{a.subject}</p>
                  <p className="text-[10px] text-muted-foreground" style={mono}>{a.code} · Sec {a.section}</p>
                </td>
                <td className="px-3 py-2.5 text-[11.5px] text-muted-foreground">{a.dept}</td>
                <td className="px-3 py-2.5">
                  <p className="text-[11px] font-medium" style={{ color: C.slate }}>{a.timeSlot}</p>
                  <p className="text-[9.5px] text-muted-foreground">{a.day}</p>
                </td>
                <td className="px-3 py-2.5 text-[12px] font-bold text-center" style={{ ...mono, color: C.slate }}>{a.units}</td>
                <td className="px-3 py-2.5">
                  <div className="flex flex-col gap-1">
                    <MatchBadge level={a.matchLevel} />
                    <span className="text-[10px] font-bold" style={{ ...mono, color: a.matchPct >= 90 ? C.green : a.matchPct >= 70 ? C.amber : C.red }}>
                      {a.matchPct}%
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2.5"><StatusBadge status={a.status} /></td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-1">
                    {a.status !== "Approved" && (
                      <button 
                        onClick={() => approve(a.id)} 
                        disabled={isUpdating === a.id}
                        title="Approve"
                        className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-green-50 transition-colors disabled:opacity-50">
                        <Check size={14} style={{ color: C.green }} />
                      </button>
                    )}
                    {a.status !== "Flagged" && (
                      <button 
                        onClick={() => flag(a.id)}
                        disabled={isUpdating === a.id}
                        title="Flag"
                        className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-red-50 transition-colors disabled:opacity-50">
                        <X size={14} style={{ color: C.red }} />
                      </button>
                    )}
                    <button onClick={() => setDetail(a)} title="View reasoning"
                      className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-[#e8faf8] transition-colors">
                      <Info size={14} style={{ color: C.teal }} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={9} className="px-4 py-8 text-center text-[12px] text-muted-foreground">No allocations match the current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Explainability Drawer */}
      {detail && (
        <>
          <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={() => setDetail(null)} />
          <div className="fixed right-0 top-0 bottom-0 z-50 w-[400px] bg-white shadow-2xl flex flex-col">
            <div className="p-5 border-b border-border" style={{ background: C.slate }}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[10px] text-white/40 mb-0.5" style={mono}>{detail.id}</p>
                  <h2 className="text-[16px] font-bold text-white">{detail.subject}</h2>
                  <p className="text-[11px] text-white/55 mt-0.5">{detail.code} · Section {detail.section}</p>
                </div>
                <button onClick={() => setDetail(null)} className="p-1.5 rounded-lg hover:bg-white/10 text-white/55 hover:text-white">
                  <X size={18} />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {/* Assignment summary */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl p-3" style={{ background: `${C.teal}10` }}>
                  <p className="text-[10px] text-muted-foreground mb-0.5">Assigned Faculty</p>
                  <p className="text-[12.5px] font-bold leading-tight" style={{ color: C.slate }}>{detail.faculty}</p>
                </div>
                <div className="rounded-xl p-3 bg-[#f0f4f8]">
                  <p className="text-[10px] text-muted-foreground mb-0.5">Schedule</p>
                  <p className="text-[12.5px] font-bold" style={{ color: C.slate }}>{detail.timeSlot}</p>
                  <p className="text-[10px] text-muted-foreground">{detail.day}</p>
                </div>
              </div>

              {/* Match visualization */}
              <div>
                <SectionHeading>Specialization Match</SectionHeading>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2.5 rounded-full bg-[#e2e8f0] overflow-hidden">
                    <div className="h-full rounded-full transition-all"
                      style={{ width: `${detail.matchPct}%`, background: detail.matchPct >= 90 ? C.green : detail.matchPct >= 70 ? C.amber : C.red }} />
                  </div>
                  <span className="text-[15px] font-bold flex-shrink-0" style={{ ...mono, color: detail.matchPct >= 90 ? C.green : detail.matchPct >= 70 ? C.amber : C.red }}>
                    {detail.matchPct}%
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <MatchBadge level={detail.matchLevel} />
                  <StatusBadge status={detail.status} />
                </div>
              </div>

              {/* Algorithm reasoning */}
              <div>
                <SectionHeading>Algorithm Justification</SectionHeading>
                <div className="rounded-xl p-4" style={{ background: `${C.teal}08`, border: `1px solid ${C.teal}25` }}>
                  <p className="text-[12px] leading-relaxed" style={{ color: C.slate }}>{detail.reason}</p>
                </div>
              </div>

              {/* Constraint checklist */}
              <div>
                <SectionHeading>Constraint Compliance</SectionHeading>
                <div className="space-y-2">
                  {[
                    { label: "Specialization match", ok: detail.matchLevel !== "Unmatched" },
                    { label: "Schedule availability confirmed", ok: true },
                    { label: "Within teaching unit limit", ok: detail.matchPct >= 70 },
                    { label: "No schedule conflict detected", ok: detail.status !== "Flagged" },
                    { label: "Department assignment valid", ok: true },
                  ].map(({ label, ok }) => (
                    <div key={label} className="flex items-center gap-2.5">
                      <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: ok ? `${C.green}18` : `${C.red}18` }}>
                        {ok ? <Check size={11} style={{ color: C.green }} /> : <X size={11} style={{ color: C.red }} />}
                      </div>
                      <span className="text-[11.5px]" style={{ color: ok ? C.slate : C.red }}>{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-border flex gap-2">
              {detail.status !== "Approved" && (
                <button onClick={() => approve(detail.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-[13px] font-bold text-white transition-colors"
                  style={{ background: C.green }}>
                  <Check size={14} /> Approve
                </button>
              )}
              {detail.status !== "Flagged" && (
                <button onClick={() => flag(detail.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl border border-border text-[13px] font-semibold text-muted-foreground hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors">
                  <X size={14} /> Flag for Review
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
