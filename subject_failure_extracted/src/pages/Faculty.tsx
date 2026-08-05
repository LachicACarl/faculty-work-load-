import { useState } from "react";
import { Search, X, Plus, Check } from "lucide-react";
import { C, mono, SectionHeading } from "../app/shared";

type EmpType = "Full-Time" | "Part-Time";

interface FacultyMember {
  id: string; name: string; dept: string; empType: EmpType;
  specializations: string[]; maxUnits: number; currentLoad: number;
  availability: Record<string, string[]>; degrees: string[];
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const SLOTS = ["7:00–8:30", "8:30–10:00", "10:00–11:30", "1:00–2:30", "2:30–4:00", "4:00–5:30"];

const FACULTY: FacultyMember[] = [
  {
    id: "FAC-001", name: "Dr. Ana Reyes", dept: "IT", empType: "Full-Time",
    specializations: ["Algorithms", "Data Structures", "Theory of Computation"],
    maxUnits: 21, currentLoad: 18, degrees: ["Ph.D. Computer Science", "M.S. Information Technology"],
    availability: { Mon: ["7:00–8:30", "8:30–10:00", "10:00–11:30"], Wed: ["7:00–8:30", "8:30–10:00"], Fri: ["1:00–2:30", "2:30–4:00"] },
  },
  {
    id: "FAC-002", name: "Prof. Luis Dela Cruz", dept: "CS", empType: "Full-Time",
    specializations: ["Machine Learning", "Data Mining", "Statistics"],
    maxUnits: 21, currentLoad: 15, degrees: ["M.S. Computer Science"],
    availability: { Tue: ["8:30–10:00", "10:00–11:30"], Thu: ["8:30–10:00", "10:00–11:30", "1:00–2:30"] },
  },
  {
    id: "FAC-003", name: "Ms. Clara Santos", dept: "Math", empType: "Full-Time",
    specializations: ["Calculus", "Linear Algebra", "Differential Equations"],
    maxUnits: 21, currentLoad: 21, degrees: ["M.S. Mathematics"],
    availability: { Mon: ["1:00–2:30", "2:30–4:00"], Wed: ["10:00–11:30", "1:00–2:30"], Fri: ["7:00–8:30"] },
  },
  {
    id: "FAC-004", name: "Dr. Jose Bautista", dept: "Physics", empType: "Full-Time",
    specializations: ["Quantum Mechanics", "Electromagnetism", "Thermodynamics"],
    maxUnits: 21, currentLoad: 12, degrees: ["Ph.D. Applied Physics"],
    availability: { Tue: ["7:00–8:30", "8:30–10:00"], Thu: ["7:00–8:30"], Fri: ["10:00–11:30", "1:00–2:30"] },
  },
  {
    id: "FAC-005", name: "Prof. Maria Torres", dept: "IT", empType: "Part-Time",
    specializations: ["Software Engineering", "Agile Methods", "UML"],
    maxUnits: 12, currentLoad: 9, degrees: ["M.S. Software Engineering"],
    availability: { Mon: ["4:00–5:30"], Wed: ["4:00–5:30"], Fri: ["4:00–5:30"] },
  },
  {
    id: "FAC-006", name: "Engr. Paolo Ramos", dept: "IT", empType: "Part-Time",
    specializations: ["Networks", "Cybersecurity", "Cloud Computing"],
    maxUnits: 12, currentLoad: 6, degrees: ["M.S. Computer Networks"],
    availability: { Tue: ["4:00–5:30"], Thu: ["4:00–5:30"] },
  },
  {
    id: "FAC-007", name: "Dr. Sofia Mendoza", dept: "CS", empType: "Full-Time",
    specializations: ["Computer Vision", "Deep Learning", "Pattern Recognition"],
    maxUnits: 21, currentLoad: 18, degrees: ["Ph.D. Computer Science", "B.S. Mathematics"],
    availability: { Mon: ["8:30–10:00", "10:00–11:30"], Thu: ["1:00–2:30", "2:30–4:00"] },
  },
  {
    id: "FAC-008", name: "Prof. Carlos Lim", dept: "Math", empType: "Part-Time",
    specializations: ["Discrete Mathematics", "Graph Theory", "Combinatorics"],
    maxUnits: 12, currentLoad: 9, degrees: ["M.S. Mathematics"],
    availability: { Wed: ["7:00–8:30", "8:30–10:00"], Fri: ["8:30–10:00", "10:00–11:30"] },
  },
];

function UtilBar({ current, max, color }: { current: number; max: number; color: string }) {
  const pct = Math.round((current / max) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-[#e2e8f0] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[10px] font-bold flex-shrink-0" style={{ ...mono, color }}>{current}/{max}u</span>
    </div>
  );
}

export default function FacultyPage() {
  const [search, setSearch] = useState("");
  const [deptFilter, setDeptFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState<"All" | EmpType>("All");
  const [selected, setSelected] = useState<FacultyMember | null>(null);
  const [editAvail, setEditAvail] = useState(false);
  const [localAvail, setLocalAvail] = useState<Record<string, string[]>>({});

  function openDrawer(f: FacultyMember) {
    setSelected(f);
    setLocalAvail({ ...f.availability });
    setEditAvail(false);
  }

  function toggleSlot(day: string, slot: string) {
    setLocalAvail((prev) => {
      const curr = prev[day] ?? [];
      const has = curr.includes(slot);
      return { ...prev, [day]: has ? curr.filter((s) => s !== slot) : [...curr, slot] };
    });
  }

  const filtered = FACULTY.filter((f) => {
    const q = search.toLowerCase();
    return (
      (!q || f.name.toLowerCase().includes(q) || f.specializations.some((s) => s.toLowerCase().includes(q))) &&
      (deptFilter === "All" || f.dept === deptFilter) &&
      (typeFilter === "All" || f.empType === typeFilter)
    );
  });

  const depts = ["All", ...Array.from(new Set(FACULTY.map((f) => f.dept)))];

  return (
    <div className="px-5 py-4 h-full flex flex-col gap-4">
      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or specialization…"
            className="w-full pl-9 pr-4 py-2 rounded-xl border border-border bg-white text-[12.5px] focus:outline-none focus:ring-2 focus:ring-teal-500/20 transition-all" />
        </div>
        <div className="flex gap-1.5">
          {depts.map((d) => (
            <button key={d} onClick={() => setDeptFilter(d)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
              style={deptFilter === d ? { background: C.slate, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}>
              {d}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          {(["All", "Full-Time", "Part-Time"] as const).map((t) => (
            <button key={t} onClick={() => setTypeFilter(t)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
              style={typeFilter === t ? { background: C.teal, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}>
              {t}
            </button>
          ))}
        </div>
        <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-[12px] font-semibold text-white ml-auto" style={{ background: C.teal }}>
          <Plus size={14} /> Add Faculty
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-black/7 shadow-sm overflow-hidden flex-1">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {["ID", "Name", "Dept", "Type", "Specializations", "Load", "Actions"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-[9.5px] font-bold uppercase tracking-wider text-muted-foreground">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((f, i) => {
              const overloaded = f.currentLoad > f.maxUnits;
              const full = f.currentLoad === f.maxUnits;
              const loadColor = overloaded ? C.red : full ? C.amber : C.teal;
              return (
                <tr key={f.id} className={`border-b border-border/50 hover:bg-[#f7fafa] transition-colors ${i % 2 === 0 ? "" : "bg-[#fafbfd]"}`}>
                  <td className="px-4 py-3 text-[10.5px] text-muted-foreground" style={mono}>{f.id}</td>
                  <td className="px-4 py-3 text-[12.5px] font-semibold" style={{ color: C.slate }}>{f.name}</td>
                  <td className="px-4 py-3 text-[12px] text-muted-foreground">{f.dept}</td>
                  <td className="px-4 py-3">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                      style={{ background: f.empType === "Full-Time" ? `${C.teal}15` : `${C.sky}15`, color: f.empType === "Full-Time" ? C.teal : C.sky }}>
                      {f.empType}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {f.specializations.slice(0, 2).map((s) => (
                        <span key={s} className="text-[9.5px] px-1.5 py-0.5 rounded-md bg-[#f0f4f8] text-muted-foreground">{s}</span>
                      ))}
                      {f.specializations.length > 2 && <span className="text-[9.5px] text-muted-foreground">+{f.specializations.length - 2}</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 min-w-[120px]">
                    <UtilBar current={f.currentLoad} max={f.maxUnits} color={loadColor} />
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => openDrawer(f)}
                      className="text-[11px] font-semibold px-2.5 py-1 rounded-lg hover:bg-[#e8faf8] transition-colors" style={{ color: C.teal }}>
                      View Profile
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Drawer */}
      {selected && (
        <>
          <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={() => setSelected(null)} />
          <div className="fixed right-0 top-0 bottom-0 z-50 w-[420px] bg-white shadow-2xl flex flex-col overflow-hidden">
            <div className="p-5 border-b border-border flex items-start justify-between" style={{ background: C.slate }}>
              <div>
                <p className="text-[10px] text-white/45 mb-0.5" style={mono}>{selected.id}</p>
                <h2 className="text-[17px] font-bold text-white">{selected.name}</h2>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="text-[11px] text-white/55">{selected.dept}</span>
                  <span className="w-1 h-1 rounded-full bg-white/25" />
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                    style={{ background: selected.empType === "Full-Time" ? `${C.teal}40` : `${C.sky}40`, color: "#fff" }}>
                    {selected.empType}
                  </span>
                </div>
              </div>
              <button onClick={() => setSelected(null)} className="p-1.5 rounded-lg hover:bg-white/10 text-white/55 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {/* Load summary */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl p-3 text-center" style={{ background: `${C.teal}10` }}>
                  <p className="text-[24px] font-bold" style={{ ...mono, color: C.teal }}>{selected.currentLoad}</p>
                  <p className="text-[10px] text-muted-foreground">Current Units</p>
                </div>
                <div className="rounded-xl p-3 text-center bg-[#f0f4f8]">
                  <p className="text-[24px] font-bold" style={{ ...mono, color: C.slate }}>{selected.maxUnits}</p>
                  <p className="text-[10px] text-muted-foreground">Max Units</p>
                </div>
              </div>

              {/* Degrees */}
              <div>
                <SectionHeading>Academic Qualifications</SectionHeading>
                <div className="space-y-1.5">
                  {selected.degrees.map((d) => (
                    <div key={d} className="flex items-center gap-2 text-[12px]" style={{ color: C.slate }}>
                      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: C.teal }} />
                      {d}
                    </div>
                  ))}
                </div>
              </div>

              {/* Specializations */}
              <div>
                <SectionHeading>Specialization Areas</SectionHeading>
                <div className="flex flex-wrap gap-1.5">
                  {selected.specializations.map((s) => (
                    <span key={s} className="text-[11px] font-medium px-2.5 py-1 rounded-lg" style={{ background: `${C.teal}12`, color: C.teal }}>{s}</span>
                  ))}
                </div>
              </div>

              {/* Availability grid */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <SectionHeading>Availability</SectionHeading>
                  <button onClick={() => setEditAvail(!editAvail)}
                    className="text-[10.5px] font-semibold px-2 py-1 rounded-lg transition-colors"
                    style={{ color: editAvail ? C.green : C.teal, background: editAvail ? `${C.green}12` : `${C.teal}12` }}>
                    {editAvail ? "Done" : "Edit"}
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-center">
                    <thead>
                      <tr>
                        <th className="text-[9px] text-muted-foreground font-medium pb-1.5 w-20 text-left">Time Slot</th>
                        {DAYS.map((d) => <th key={d} className="text-[9px] text-muted-foreground font-medium pb-1.5 w-10">{d}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {SLOTS.map((slot) => (
                        <tr key={slot}>
                          <td className="text-left pr-2 py-0.5">
                            <span className="text-[9px] text-muted-foreground" style={mono}>{slot}</span>
                          </td>
                          {DAYS.map((day) => {
                            const avail = (localAvail[day] ?? []).includes(slot);
                            return (
                              <td key={day} className="py-0.5 px-0.5">
                                <button
                                  onClick={() => editAvail && toggleSlot(day, slot)}
                                  disabled={!editAvail}
                                  className="w-7 h-6 rounded-md mx-auto flex items-center justify-center transition-all"
                                  style={{ background: avail ? `${C.teal}20` : "#f0f4f8", cursor: editAvail ? "pointer" : "default" }}>
                                  {avail && <Check size={10} style={{ color: C.teal }} />}
                                </button>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-border flex gap-2">
              <button className="flex-1 py-2 rounded-xl border border-border text-[12px] font-semibold text-muted-foreground hover:bg-muted transition-colors">Edit Profile</button>
              <button className="flex-1 py-2 rounded-xl text-[12px] font-bold text-white transition-colors" style={{ background: C.teal }}>Save Availability</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
