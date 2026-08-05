import { useEffect, useState } from "react";
import { Search, X, Plus, Check } from "lucide-react";
import { C, mono, SectionHeading } from "../app/shared";

type EmpType = "Full-Time" | "Part-Time";

interface FacultyMember {
  id: string;
  name: string;
  dept: string;
  empType: EmpType;
  specializations: string[];
  maxUnits: number;
  currentLoad: number;
  availability: Record<string, string[]>;
  degrees: string[];
}

type FacultyApiRecord = {
  id: string;
  name: string;
  department?: string;
  employment_type?: string;
  specializations?: string[];
  min_units?: number;
  max_units?: number;
  current_load?: number;
  degrees?: string[];
  availability?: Record<string, string[]>;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const SLOTS = ["7:00–8:30", "8:30–10:00", "10:00–11:30", "1:00–2:30", "2:30–4:00", "4:00–5:30"];
const EMPLOYMENT_TYPES = ["All", "Full-Time", "Part-Time"] as const;
const EMPTY_AVAILABILITY = { Mon: [], Tue: [], Wed: [], Thu: [], Fri: [] };
const DEFAULT_PROFILE_DRAFT = { name: "", dept: "", empType: "Full-Time" as EmpType };

function createEmptyAvailability(): Record<string, string[]> {
  return { ...EMPTY_AVAILABILITY };
}

function isPartTimeEmploymentType(value?: string) {
  return Boolean(value?.toLowerCase().startsWith("part"));
}

function nextFacultyId(facultyList: FacultyMember[]) {
  const next = facultyList.reduce((highest, item) => {
    const match = item.id.match(/(\d+)$/);
    const value = match ? Number(match[1]) : 0;
    return Math.max(highest, value);
  }, 0) + 1;
  return `FAC-${String(next).padStart(3, "0")}`;
}

function toFacultyMember(record: FacultyApiRecord): FacultyMember {
  return {
    id: record.id,
    name: record.name,
    dept: record.department ?? "Unknown",
    empType: isPartTimeEmploymentType(record.employment_type) ? "Part-Time" : "Full-Time",
    specializations: record.specializations ?? [],
    maxUnits: Number(record.max_units ?? 0),
    currentLoad: Number(record.current_load ?? 0),
    degrees: record.degrees ?? [],
    availability: record.availability ?? createEmptyAvailability(),
  };
}

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

function FacultyFilters({
  search,
  setSearch,
  deptFilter,
  setDeptFilter,
  typeFilter,
  setTypeFilter,
  depts,
  onAddFaculty,
}: {
  search: string;
  setSearch: (value: string) => void;
  deptFilter: string;
  setDeptFilter: (value: string) => void;
  typeFilter: "All" | EmpType;
  setTypeFilter: (value: "All" | EmpType) => void;
  depts: string[];
  onAddFaculty: () => void;
}) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="relative flex-1 min-w-[200px]">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or specialization…"
          className="w-full pl-9 pr-4 py-2 rounded-xl border border-border bg-white text-[12.5px] focus:outline-none focus:ring-2 focus:ring-teal-500/20 transition-all"
        />
      </div>

      <div className="flex gap-1.5">
        {depts.map((d) => (
          <button
            key={d}
            onClick={() => setDeptFilter(d)}
            className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
            style={deptFilter === d ? { background: C.slate, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}
          >
            {d}
          </button>
        ))}
      </div>

      <div className="flex gap-1.5">
        {EMPLOYMENT_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setTypeFilter(type)}
            className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
            style={typeFilter === type ? { background: C.teal, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}
          >
            {type}
          </button>
        ))}
      </div>

      <button
        onClick={onAddFaculty}
        className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-[12px] font-semibold text-white ml-auto"
        style={{ background: C.teal }}
      >
        <Plus size={14} /> Add Faculty
      </button>
    </div>
  );
}

function FacultySummaryBanner({ feedback }: { feedback: string | null }) {
  if (!feedback) {
    return null;
  }

  return (
    <div className="rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-[12px] text-teal-800">
      {feedback}
    </div>
  );
}

function FacultyLoadingState({ loading }: { loading: boolean }) {
  if (!loading) {
    return null;
  }

  return (
    <div className="rounded-xl border border-border bg-white px-4 py-6 text-[12px] text-muted-foreground">
      Loading faculty roster...
    </div>
  );
}

function FacultyTable({
  loading,
  filtered,
  onOpenDrawer,
}: {
  loading: boolean;
  filtered: FacultyMember[];
  onOpenDrawer: (faculty: FacultyMember) => void;
}) {
  return (
    <div className="bg-white rounded-xl border border-black/7 shadow-sm overflow-hidden flex-1">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            { ["ID", "Name", "Dept", "Type", "Specializations", "Load", "Actions"].map((heading) => (
              <th key={heading} className="text-left px-4 py-3 text-[9.5px] font-bold uppercase tracking-wider text-muted-foreground">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {!loading && filtered.map((faculty, index) => {
            const overloaded = faculty.currentLoad > faculty.maxUnits;
            const full = faculty.currentLoad === faculty.maxUnits;
            const loadColor = overloaded ? C.red : full ? C.amber : C.teal;

            return (
              <tr key={faculty.id} className={`border-b border-border/50 hover:bg-[#f7fafa] transition-colors ${index % 2 === 0 ? "" : "bg-[#fafbfd]"}`}>
                <td className="px-4 py-3 text-[10.5px] text-muted-foreground" style={mono}>{faculty.id}</td>
                <td className="px-4 py-3 text-[12.5px] font-semibold" style={{ color: C.slate }}>{faculty.name}</td>
                <td className="px-4 py-3 text-[12px] text-muted-foreground">{faculty.dept}</td>
                <td className="px-4 py-3">
                  <span
                    className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    style={{ background: faculty.empType === "Full-Time" ? `${C.teal}15` : `${C.sky}15`, color: faculty.empType === "Full-Time" ? C.teal : C.sky }}
                  >
                    {faculty.empType}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {faculty.specializations.slice(0, 2).map((specialization) => (
                      <span key={specialization} className="text-[9.5px] px-1.5 py-0.5 rounded-md bg-[#f0f4f8] text-muted-foreground">
                        {specialization}
                      </span>
                    ))}
                    {faculty.specializations.length > 2 && <span className="text-[9.5px] text-muted-foreground">+{faculty.specializations.length - 2}</span>}
                  </div>
                </td>
                <td className="px-4 py-3 min-w-[120px]">
                  <UtilBar current={faculty.currentLoad} max={faculty.maxUnits} color={loadColor} />
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => onOpenDrawer(faculty)}
                    className="text-[11px] font-semibold px-2.5 py-1 rounded-lg hover:bg-[#e8faf8] transition-colors"
                    style={{ color: C.teal }}
                  >
                    View Profile
                  </button>
                </td>
              </tr>
            );
          })}

          {!loading && filtered.length === 0 && (
            <tr>
              <td colSpan={7} className="px-4 py-10 text-center text-[12px] text-muted-foreground">
                No faculty match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function FacultyDrawer({
  selected,
  editProfile,
  setEditProfile,
  editAvail,
  setEditAvail,
  profileDraft,
  setProfileDraft,
  localAvail,
  toggleSlot,
  saveAvailability,
  onClose,
}: {
  selected: FacultyMember;
  editProfile: boolean;
  setEditProfile: (value: boolean | ((current: boolean) => boolean)) => void;
  editAvail: boolean;
  setEditAvail: (value: boolean | ((current: boolean) => boolean)) => void;
  profileDraft: { name: string; dept: string; empType: EmpType };
  setProfileDraft: React.Dispatch<React.SetStateAction<{ name: string; dept: string; empType: EmpType }>>;
  localAvail: Record<string, string[]>;
  toggleSlot: (day: string, slot: string) => void;
  saveAvailability: () => void;
  onClose: () => void;
}) {
  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 z-50 w-full md:w-[min(1400px,98vw)] bg-white shadow-2xl flex flex-col overflow-hidden md:rounded-l-2xl">
        <div className="p-5 border-b border-border flex items-start justify-between" style={{ background: C.slate }}>
          <div>
            <p className="text-[10px] text-white/45 mb-0.5" style={mono}>{selected.id}</p>
            <h2 className="text-[17px] font-bold text-white">{selected.name}</h2>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-[11px] text-white/55">{selected.dept}</span>
              <span className="w-1 h-1 rounded-full bg-white/25" />
              <span
                className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                style={{ background: selected.empType === "Full-Time" ? `${C.teal}40` : `${C.sky}40`, color: "#fff" }}
              >
                {selected.empType}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/10 text-white/55 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 sm:p-5 space-y-4 sm:space-y-5">
          {editProfile && (
            <div className="rounded-2xl border border-teal-200 bg-teal-50/60 p-4 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: C.teal }}>Edit Profile</p>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: `${C.teal}15`, color: C.teal }}>
                  Changes apply locally
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label className="space-y-1">
                  <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Name</span>
                  <input
                    value={profileDraft.name}
                    onChange={(e) => setProfileDraft((prev) => ({ ...prev, name: e.target.value }))}
                    className="w-full rounded-xl border border-border px-3 py-2 text-[12px] focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                </label>
                <label className="space-y-1">
                  <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Department</span>
                  <input
                    value={profileDraft.dept}
                    onChange={(e) => setProfileDraft((prev) => ({ ...prev, dept: e.target.value }))}
                    className="w-full rounded-xl border border-border px-3 py-2 text-[12px] focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                </label>
              </div>

              <div className="flex gap-2 flex-wrap">
                {(["Full-Time", "Part-Time"] as const).map((type) => (
                  <button
                    key={type}
                    onClick={() => setProfileDraft((prev) => ({ ...prev, empType: type }))}
                    className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-colors"
                    style={profileDraft.empType === type ? { background: C.teal, color: "#fff" } : { background: "#fff", color: "#64748b", border: "1px solid #e2e8f0" }}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="rounded-xl p-3 text-center" style={{ background: `${C.teal}10` }}>
              <p className="text-[24px] font-bold" style={{ ...mono, color: C.teal }}>{selected.currentLoad}</p>
              <p className="text-[10px] text-muted-foreground">Current Units</p>
            </div>
            <div className="rounded-xl p-3 text-center bg-[#f0f4f8]">
              <p className="text-[24px] font-bold" style={{ ...mono, color: C.slate }}>{selected.maxUnits}</p>
              <p className="text-[10px] text-muted-foreground">Max Units</p>
            </div>
          </div>

          <div>
            <SectionHeading>Academic Qualifications</SectionHeading>
            <div className="space-y-1.5">
              {selected.degrees.map((degree) => (
                <div key={degree} className="flex items-center gap-2 text-[12px]" style={{ color: C.slate }}>
                  <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: C.teal }} />
                  {degree}
                </div>
              ))}
            </div>
          </div>

          <div>
            <SectionHeading>Specialization Areas</SectionHeading>
            <div className="flex flex-wrap gap-1.5">
              {selected.specializations.map((specialization) => (
                <span key={specialization} className="text-[11px] font-medium px-2.5 py-1 rounded-lg" style={{ background: `${C.teal}12`, color: C.teal }}>
                  {specialization}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <SectionHeading>Availability</SectionHeading>
              <button
                onClick={() => setEditAvail((current) => !current)}
                className="text-[10.5px] font-semibold px-2 py-1 rounded-lg transition-colors"
                style={{ color: editAvail ? C.green : C.teal, background: editAvail ? `${C.green}12` : `${C.teal}12` }}
              >
                {editAvail ? "Done" : "Edit"}
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-center">
                <thead>
                  <tr>
                    <th className="text-[9px] text-muted-foreground font-medium pb-1.5 w-20 text-left">Time Slot</th>
                    {DAYS.map((day) => (
                      <th key={day} className="text-[9px] text-muted-foreground font-medium pb-1.5 w-10">{day}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SLOTS.map((slot) => (
                    <tr key={slot}>
                      <td className="text-left pr-2 py-0.5">
                        <span className="text-[9px] text-muted-foreground" style={mono}>{slot}</span>
                      </td>
                      {DAYS.map((day) => {
                        const available = (localAvail[day] ?? []).includes(slot);
                        return (
                          <td key={day} className="py-0.5 px-0.5">
                            <button
                              onClick={() => editAvail && toggleSlot(day, slot)}
                              disabled={!editAvail}
                              className="w-7 h-6 rounded-md mx-auto flex items-center justify-center transition-all"
                              style={{ background: available ? `${C.teal}20` : "#f0f4f8", cursor: editAvail ? "pointer" : "default" }}
                            >
                              {available && <Check size={10} style={{ color: C.teal }} />}
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
          <button
            onClick={() => setEditProfile((current) => !current)}
            className="flex-1 py-2 rounded-xl border border-border text-[12px] font-semibold text-muted-foreground hover:bg-muted transition-colors"
          >
            {editProfile ? "Cancel Edit" : "Edit Profile"}
          </button>
          <button onClick={saveAvailability} className="flex-1 py-2 rounded-xl text-[12px] font-bold text-white transition-colors" style={{ background: C.teal }}>
            Save Availability
          </button>
        </div>
      </div>
    </>
  );
}

export default function FacultyPage() {
  // Search and filters
  const [search, setSearch] = useState("");
  const [deptFilter, setDeptFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState<"All" | EmpType>("All");

  // Selection and drawer state
  const [selected, setSelected] = useState<FacultyMember | null>(null);
  const [editAvail, setEditAvail] = useState(false);
  const [editProfile, setEditProfile] = useState(false);
  const [localAvail, setLocalAvail] = useState<Record<string, string[]>>({});

  // Remote faculty data and feedback
  const [profileDraft, setProfileDraft] = useState(DEFAULT_PROFILE_DRAFT);
  const [facultyList, setFacultyList] = useState<FacultyMember[]>([]);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadFaculty() {
      setLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/faculty`);
        if (!response.ok) {
          throw new Error("Unable to load faculty roster");
        }

        const payload = await response.json();
        if (active) {
          const normalized = Array.isArray(payload) ? payload.map((item) => toFacultyMember(item)) : [];
          setFacultyList(normalized);
          if (normalized.length > 0) {
            openDrawer(normalized[0]);
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to load faculty roster";
        setFeedback(message);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadFaculty();
    return () => {
      active = false;
    };
  }, []);

  function openDrawer(f: FacultyMember) {
    setSelected(f);
    setLocalAvail({ ...f.availability });
    setProfileDraft({ name: f.name, dept: f.dept, empType: f.empType });
    setEditAvail(false);
    setEditProfile(false);
  }

  function toggleSlot(day: string, slot: string) {
    setLocalAvail((prev) => {
      const curr = prev[day] ?? [];
      const has = curr.includes(slot);
      return { ...prev, [day]: has ? curr.filter((s) => s !== slot) : [...curr, slot] };
    });
  }

  const filtered = facultyList.filter((f) => {
    const q = search.toLowerCase();
    return (
      (!q || f.name.toLowerCase().includes(q) || f.specializations.some((s) => s.toLowerCase().includes(q))) &&
      (deptFilter === "All" || f.dept === deptFilter) &&
      (typeFilter === "All" || f.empType === typeFilter)
    );
  });

  const depts = ["All", ...Array.from(new Set(facultyList.map((f) => f.dept)))];

  function addFaculty() {
    const id = nextFacultyId(facultyList);
    const newFaculty: FacultyMember = {
      id,
      name: "New Faculty Member",
      dept: "IT",
      empType: "Full-Time",
      specializations: ["New Specialization"],
      maxUnits: 18,
      currentLoad: 0,
      availability: createEmptyAvailability(),
      degrees: ["TBA"],
    };

    void fetch(`${API_BASE_URL}/api/faculty`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id,
        name: newFaculty.name,
        department: newFaculty.dept,
        employment_type: newFaculty.empType,
        specializations: newFaculty.specializations,
        min_units: 0,
        max_units: newFaculty.maxUnits,
        current_load: newFaculty.currentLoad,
        degrees: newFaculty.degrees,
        availability: newFaculty.availability,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const failed = await response.json().catch(() => ({ detail: "Unable to create faculty" }));
          throw new Error(failed.detail ?? "Unable to create faculty");
        }

        const created = toFacultyMember(await response.json());
        setFacultyList((prev) => [...prev, created]);
        setSelected(created);
        setLocalAvail({ Mon: [], Tue: [], Wed: [], Thu: [], Fri: [] });
        setEditAvail(false);
        setEditProfile(false);
        setProfileDraft({ name: created.name, dept: created.dept, empType: created.empType });
        setFeedback(`${created.id} created.`);
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : "Unable to create faculty";
        setFeedback(message);
      });
  }

  function saveAvailability() {
    if (!selected) {
      return;
    }

    void fetch(`${API_BASE_URL}/api/faculty/${selected.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: profileDraft.name.trim() || selected.name,
        department: profileDraft.dept.trim() || selected.dept,
        employment_type: profileDraft.empType,
        availability: localAvail,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const failed = await response.json().catch(() => ({ detail: "Unable to save faculty" }));
          throw new Error(failed.detail ?? "Unable to save faculty");
        }

        const updated = toFacultyMember(await response.json());
        setFacultyList((prev) => prev.map((item) => item.id === updated.id ? updated : item));
        setSelected(updated);
        setProfileDraft({ name: updated.name, dept: updated.dept, empType: updated.empType });
        setFeedback(`Availability saved for ${updated.name}.`);
        setEditProfile(false);
        setEditAvail(false);
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : "Unable to save faculty";
        setFeedback(message);
      });
  }

  return (
    <div className="px-5 py-4 h-full flex flex-col gap-4">
      <FacultyFilters
        search={search}
        setSearch={setSearch}
        deptFilter={deptFilter}
        setDeptFilter={setDeptFilter}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        depts={depts}
        onAddFaculty={addFaculty}
      />

      <FacultySummaryBanner feedback={feedback} />
      <FacultyLoadingState loading={loading} />
      <FacultyTable loading={loading} filtered={filtered} onOpenDrawer={openDrawer} />

      {selected && (
        <FacultyDrawer
          selected={selected}
          editProfile={editProfile}
          setEditProfile={setEditProfile}
          editAvail={editAvail}
          setEditAvail={setEditAvail}
          profileDraft={profileDraft}
          setProfileDraft={setProfileDraft}
          localAvail={localAvail}
          toggleSlot={toggleSlot}
          saveAvailability={saveAvailability}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
