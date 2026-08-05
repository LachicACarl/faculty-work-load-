import { useState } from "react";
import { Search, Download, X, TrendingUp, BookOpen, Calendar, ChevronRight } from "lucide-react";
import { C, mono, RiskBadge, SectionHeading } from "../app/shared";

type RiskLevel = "High" | "Moderate" | "Low";

interface Student {
  id: string; name: string; year: string;
  subjects: string[]; probability: number; risk: RiskLevel;
}

const STUDENTS: Student[] = [
  { id: "2021-00142", name: "Juan Miguel Santos", year: "3rd Year", subjects: ["Math", "Physics", "Prog. 2"], probability: 84, risk: "High" },
  { id: "2021-00158", name: "Andrea Lim", year: "3rd Year", subjects: ["Calc. 2", "Discrete Math"], probability: 67, risk: "Moderate" },
  { id: "2022-00031", name: "Rafael Mendoza", year: "2nd Year", subjects: ["Math", "Physics"], probability: 91, risk: "High" },
  { id: "2022-00047", name: "Sofia Cruz", year: "2nd Year", subjects: ["Prog. 2", "Discrete Math"], probability: 23, risk: "Low" },
  { id: "2020-00089", name: "Carlos Reyes", year: "4th Year", subjects: ["Calc. 2"], probability: 72, risk: "High" },
  { id: "2021-00203", name: "Maria Gonzales", year: "3rd Year", subjects: ["Math", "Prog. 2", "Physics"], probability: 55, risk: "Moderate" },
  { id: "2023-00011", name: "Paolo Bautista", year: "1st Year", subjects: ["Math", "Physics"], probability: 18, risk: "Low" },
  { id: "2022-00094", name: "Camille Torres", year: "2nd Year", subjects: ["Discrete Math", "Calc. 2"], probability: 61, risk: "Moderate" },
  { id: "2021-00177", name: "Marco Dela Cruz", year: "3rd Year", subjects: ["Math", "Prog. 2"], probability: 88, risk: "High" },
  { id: "2023-00028", name: "Bianca Ramos", year: "1st Year", subjects: ["Physics"], probability: 12, risk: "Low" },
];

const SUBJECT_OPTS = ["All Subjects", "Math", "Physics", "Prog. 2", "Discrete Math", "Calc. 2"];
const RISK_OPTS: Array<"All" | RiskLevel> = ["All", "High", "Moderate", "Low"];

const GRADE_DATA: Record<string, { subject: string; midterm: number; finals: number; attendance: number }[]> = {
  "2021-00142": [
    { subject: "Math", midterm: 64, finals: 58, attendance: 72 },
    { subject: "Physics", midterm: 55, finals: 52, attendance: 68 },
    { subject: "Prog. 2", midterm: 61, finals: 55, attendance: 75 },
  ],
  default: [
    { subject: "Main Subject", midterm: 71, finals: 68, attendance: 80 },
  ],
};

export default function Students() {
  const [search, setSearch] = useState("");
  const [yearFilter, setYearFilter] = useState("All Years");
  const [subjectFilter, setSubjectFilter] = useState("All Subjects");
  const [riskFilter, setRiskFilter] = useState<"All" | RiskLevel>("All");
  const [drawer, setDrawer] = useState<Student | null>(null);

  const filtered = STUDENTS.filter((s) => {
    const q = search.toLowerCase();
    const matchSearch = !q || s.name.toLowerCase().includes(q) || s.id.includes(q) || s.subjects.some((x) => x.toLowerCase().includes(q));
    const matchRisk = riskFilter === "All" || s.risk === riskFilter;
    const matchSubject = subjectFilter === "All Subjects" || s.subjects.includes(subjectFilter);
    return matchSearch && matchRisk && matchSubject;
  });

  const grades = drawer ? (GRADE_DATA[drawer.id] ?? GRADE_DATA.default) : [];

  return (
    <div className="px-5 py-4 h-full flex flex-col">
      {/* Top bar */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by student name, ID, or course..."
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-border bg-white text-[12.5px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
          />
        </div>
        <select value={yearFilter} onChange={(e) => setYearFilter(e.target.value)} className="px-3 py-2 rounded-xl border border-border bg-white text-[12.5px] focus:outline-none cursor-pointer">
          {["All Years", "1st Year", "2nd Year", "3rd Year", "4th Year"].map((y) => <option key={y}>{y}</option>)}
        </select>
        <select value={subjectFilter} onChange={(e) => setSubjectFilter(e.target.value)} className="px-3 py-2 rounded-xl border border-border bg-white text-[12.5px] focus:outline-none cursor-pointer">
          {SUBJECT_OPTS.map((s) => <option key={s}>{s}</option>)}
        </select>
        <div className="flex gap-1.5">
          {RISK_OPTS.map((r) => (
            <button
              key={r}
              onClick={() => setRiskFilter(r)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
              style={riskFilter === r
                ? { background: C.navy, color: "#fff" }
                : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}
            >
              {r}
            </button>
          ))}
        </div>
        <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border bg-white text-[12.5px] font-medium hover:bg-muted transition-colors ml-auto">
          <Download size={14} />
          Export Roster
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-black/7 shadow-sm overflow-hidden flex-1">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {["Student ID", "Full Name", "Year Level", "Enrolled Subjects", "Failure Prob.", "Risk Status", "Actions"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-[9.5px] font-bold uppercase tracking-wider text-muted-foreground">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((s, i) => (
              <tr key={s.id} className={`border-b border-border/50 hover:bg-[#f7f9fd] transition-colors ${i % 2 === 0 ? "" : "bg-[#fafbfd]"}`}>
                <td className="px-4 py-3 text-[11px] text-muted-foreground" style={mono}>{s.id}</td>
                <td className="px-4 py-3 text-[12.5px] font-semibold" style={{ color: C.navy }}>{s.name}</td>
                <td className="px-4 py-3 text-[12px] text-muted-foreground">{s.year}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {s.subjects.map((sub) => (
                      <span key={sub} className="text-[9.5px] px-1.5 py-0.5 rounded-md bg-[#edf0f7] text-muted-foreground font-medium">{sub}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-[13px] font-bold" style={{ ...mono, color: s.probability >= 75 ? C.high : s.probability >= 50 ? C.moderate : C.low }}>
                    {s.probability}%
                  </span>
                </td>
                <td className="px-4 py-3"><RiskBadge level={s.risk} /></td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => setDrawer(s)}
                    className="flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-lg transition-colors hover:bg-[#edf0f7]"
                    style={{ color: C.blue }}
                  >
                    View Profile <ChevronRight size={12} />
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-[12px] text-muted-foreground">No students match the current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Side Drawer */}
      {drawer && (
        <>
          <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={() => setDrawer(null)} />
          <div className="fixed right-0 top-0 bottom-0 z-50 w-[380px] bg-white shadow-2xl flex flex-col">
            {/* Drawer header */}
            <div className="flex items-start justify-between p-5 border-b border-border" style={{ background: C.navy }}>
              <div>
                <p className="text-[11px] text-white/50 mb-0.5" style={mono}>{drawer.id}</p>
                <h2 className="text-[17px] font-bold text-white">{drawer.name}</h2>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-[11px] text-white/60">{drawer.year}</span>
                  <span className="w-1 h-1 rounded-full bg-white/30" />
                  <RiskBadge level={drawer.risk} />
                </div>
              </div>
              <button onClick={() => setDrawer(null)} className="p-1.5 rounded-lg hover:bg-white/10 text-white/60 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {/* Summary stat */}
              <div className="flex gap-3">
                <div className="flex-1 rounded-xl p-3 text-center" style={{ background: `${drawer.probability >= 75 ? C.high : drawer.probability >= 50 ? C.moderate : C.low}12` }}>
                  <p className="text-[28px] font-bold" style={{ ...mono, color: drawer.probability >= 75 ? C.high : drawer.probability >= 50 ? C.moderate : C.low }}>{drawer.probability}%</p>
                  <p className="text-[10px] text-muted-foreground">Failure Probability</p>
                </div>
                <div className="flex-1 rounded-xl p-3 text-center bg-[#f0f3f9]">
                  <p className="text-[28px] font-bold" style={{ ...mono, color: C.navy }}>{drawer.subjects.length}</p>
                  <p className="text-[10px] text-muted-foreground">Enrolled Subjects</p>
                </div>
              </div>

              {/* Grade trajectories */}
              <div>
                <SectionHeading>Grade Trajectories</SectionHeading>
                <div className="space-y-3">
                  {grades.map((g) => (
                    <div key={g.subject} className="bg-[#f7f9fd] rounded-xl p-3">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-[12px] font-semibold" style={{ color: C.navy }}>{g.subject}</p>
                        <span className="text-[10px] text-muted-foreground">Attendance: <strong style={mono}>{g.attendance}%</strong></span>
                      </div>
                      <div className="flex gap-3">
                        {[["Midterm", g.midterm], ["Finals", g.finals]].map(([label, score]) => (
                          <div key={label as string} className="flex-1">
                            <p className="text-[9px] uppercase tracking-wider text-muted-foreground mb-1">{label}</p>
                            <div className="h-1.5 rounded-full bg-[#e4eaf4] overflow-hidden">
                              <div className="h-full rounded-full" style={{ width: `${score}%`, background: (score as number) < 60 ? C.high : (score as number) < 75 ? C.moderate : C.low }} />
                            </div>
                            <p className="text-[11px] font-bold mt-1" style={{ ...mono, color: C.navy }}>{score}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Attendance log */}
              <div>
                <SectionHeading>Recent Attendance</SectionHeading>
                <div className="flex flex-wrap gap-1.5">
                  {Array.from({ length: 20 }, (_, i) => {
                    const type = i < 2 ? "absent" : i < 5 ? "late" : "present";
                    return (
                      <div key={i} className="w-6 h-6 rounded flex items-center justify-center text-[8px] font-bold"
                        style={{ background: type === "absent" ? `${C.high}20` : type === "late" ? `${C.moderate}20` : `${C.low}18`, color: type === "absent" ? C.high : type === "late" ? C.moderate : C.low }}>
                        {type === "absent" ? "A" : type === "late" ? "L" : "P"}
                      </div>
                    );
                  })}
                </div>
                <div className="flex gap-4 mt-2">
                  {[["P", "Present", C.low], ["L", "Late", C.moderate], ["A", "Absent", C.high]].map(([code, label, color]) => (
                    <div key={code as string} className="flex items-center gap-1">
                      <span className="text-[9px] font-bold" style={{ color: color as string }}>{code}</span>
                      <span className="text-[9px] text-muted-foreground">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-border flex gap-2">
              <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl border border-border text-[12px] font-semibold text-muted-foreground hover:bg-muted transition-colors">
                <TrendingUp size={14} /> Track Progress
              </button>
              <button className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-[12px] font-semibold text-white transition-colors" style={{ background: C.blue }}>
                <BookOpen size={14} /> Assign Intervention
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
