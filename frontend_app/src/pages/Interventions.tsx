import { useState } from "react";
import { ClipboardList, Clock, CheckCircle2, AlertCircle, Plus, ChevronDown } from "lucide-react";
import { C, mono, RiskBadge, SectionHeading } from "../app/shared";

type Status = "Pending" | "In Progress" | "Completed";
type IntType = "Counseling" | "Tutorial" | "Faculty Consultation" | "Progress Monitoring";

interface InterventionCard {
  id: string; student: string; initials: string;
  subject: string; risk: "High" | "Moderate" | "Low";
  type: IntType; assignee: string; progress?: number;
  outcome?: string; date: string;
}

const ITEMS: InterventionCard[] = [
  { id: "INT-001", student: "Juan Miguel Santos", initials: "JM", subject: "Prog. 2", risk: "High", type: "Counseling", assignee: "Dr. Reyes", date: "Jul 10" },
  { id: "INT-002", student: "Rafael Mendoza", initials: "RM", subject: "Physics", risk: "High", type: "Faculty Consultation", assignee: "Prof. Dela Cruz", date: "Jul 9" },
  { id: "INT-003", student: "Carlos Reyes", initials: "CR", subject: "Calc. 2", risk: "High", type: "Tutorial", assignee: "Ms. Santos", date: "Jul 8" },
  { id: "INT-004", student: "Andrea Lim", initials: "AL", subject: "Calc. 2", risk: "Moderate", type: "Progress Monitoring", assignee: "Prof. Garcia", progress: 60, date: "Jul 6" },
  { id: "INT-005", student: "Maria Gonzales", initials: "MG", subject: "Math", risk: "Moderate", type: "Tutorial", assignee: "Ms. Santos", progress: 35, date: "Jul 5" },
  { id: "INT-006", student: "Marco Dela Cruz", initials: "MD", subject: "Math", risk: "High", type: "Counseling", assignee: "Dr. Reyes", progress: 80, date: "Jul 4" },
  { id: "INT-007", student: "Camille Torres", initials: "CT", subject: "Discrete Math", risk: "Moderate", type: "Faculty Consultation", assignee: "Prof. Dela Cruz", progress: 50, date: "Jul 3" },
  { id: "INT-008", student: "Sofia Cruz", initials: "SC", subject: "Prog. 2", risk: "Low", type: "Tutorial", assignee: "Ms. Santos", outcome: "Grade improved to passing", date: "Jun 28" },
  { id: "INT-009", student: "Paolo Bautista", initials: "PB", subject: "Math", risk: "Low", type: "Progress Monitoring", assignee: "Prof. Garcia", outcome: "Student back on track", date: "Jun 25" },
  { id: "INT-010", student: "Bianca Ramos", initials: "BR", subject: "Physics", risk: "Low", type: "Counseling", assignee: "Dr. Reyes", outcome: "Participation improved", date: "Jun 20" },
];

const STATUSES: Status[] = ["Pending", "In Progress", "Completed"];
const STATUS_ICONS = { Pending: AlertCircle, "In Progress": Clock, Completed: CheckCircle2 };
const STATUS_COLORS = { Pending: C.moderate, "In Progress": C.blue, Completed: C.low };

function getByStatus(status: Status) {
  if (status === "Pending") return ITEMS.slice(0, 3);
  if (status === "In Progress") return ITEMS.slice(3, 7);
  return ITEMS.slice(7);
}

const TYPE_COLORS: Record<IntType, string> = {
  Counseling: C.blue, Tutorial: C.low,
  "Faculty Consultation": C.moderate, "Progress Monitoring": C.purple,
};

const metrics = [
  { label: "Total Assigned", value: 101, color: C.navy, Icon: ClipboardList },
  { label: "In Progress", value: 34, color: C.blue, Icon: Clock },
  { label: "Pending Review", value: 26, color: C.moderate, Icon: AlertCircle },
  { label: "Completed", value: 41, color: C.low, Icon: CheckCircle2 },
];

export default function Interventions() {
  const [activeTab, setActiveTab] = useState<Status>("Pending");
  const [expandedOutcome, setExpandedOutcome] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const items = getByStatus(activeTab);
  const StatusIcon = STATUS_ICONS[activeTab];

  function assignAction(kind: string, student: string) {
    setStatusMessage(`${kind} assigned to ${student}.`);
  }

  return (
    <div className="px-5 py-4 space-y-4">
      {/* Metrics strip */}
      <div className="grid grid-cols-4 gap-3">
        {metrics.map(({ label, value, color, Icon }) => (
          <div key={label} className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${color}18` }}>
              <Icon size={18} style={{ color }} />
            </div>
            <div>
              <p className="text-[24px] font-bold leading-none" style={{ ...mono, color }}>{value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl border border-black/7 shadow-sm overflow-hidden">
        <div className="flex border-b border-border">
          {STATUSES.map((s) => {
            const Icon = STATUS_ICONS[s];
            const active = activeTab === s;
            return (
              <button
                key={s}
                onClick={() => setActiveTab(s)}
                className="flex-1 flex items-center justify-center gap-2 py-3 text-[12.5px] font-semibold transition-all border-b-2"
                style={{ borderColor: active ? STATUS_COLORS[s] : "transparent", color: active ? STATUS_COLORS[s] : "#64748b", background: active ? `${STATUS_COLORS[s]}06` : "transparent" }}
              >
                <Icon size={14} />
                {s}
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold" style={{ background: `${STATUS_COLORS[s]}18`, color: STATUS_COLORS[s] }}>
                  {getByStatus(s).length}
                </span>
              </button>
            );
          })}
        </div>

        <div className="p-4 space-y-3">
          {statusMessage && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-2 text-[11px] text-blue-800">
              {statusMessage}
            </div>
          )}
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border p-4 transition-all"
              style={{ borderColor: "#f0f3f9", background: "#fafbfd" }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-white text-[10px] font-bold"
                  style={{ background: STATUS_COLORS[activeTab] }}
                >
                  {item.initials}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-[13px] font-semibold" style={{ color: C.navy }}>{item.student}</p>
                      <p className="text-[11px] text-muted-foreground">{item.subject} · {item.date}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <RiskBadge level={item.risk} />
                      <span
                        className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                        style={{ background: `${TYPE_COLORS[item.type]}15`, color: TYPE_COLORS[item.type] }}
                      >
                        {item.type}
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-muted-foreground mt-1.5">
                    Assigned to: <span className="font-semibold text-foreground">{item.assignee}</span>
                  </p>

                  {/* Progress bar */}
                  {item.progress !== undefined && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[9.5px] text-muted-foreground">Progress</span>
                        <span className="text-[10px] font-bold" style={{ ...mono, color: C.blue }}>{item.progress}%</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-[#e4eaf4] overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${item.progress}%`, background: C.blue }} />
                      </div>
                    </div>
                  )}

                  {/* Outcome */}
                  {item.outcome && (
                    <div className="mt-2 rounded-lg p-2.5" style={{ background: `${C.low}12` }}>
                      <p className="text-[10.5px] font-medium" style={{ color: C.low }}>
                        Outcome: {item.outcome}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions for Pending */}
              {activeTab === "Pending" && (
                <div className="flex gap-2 mt-3 pl-12">
                  <button onClick={() => assignAction("Counseling", item.student)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold text-white transition-colors" style={{ background: C.blue }}>
                    <Plus size={12} /> Assign Counseling
                  </button>
                  <button onClick={() => assignAction("Tutorial", item.student)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold border border-border text-muted-foreground hover:bg-muted transition-colors">
                    <Plus size={12} /> Assign Tutorial
                  </button>
                </div>
              )}

              {/* Outcome note for completed */}
              {activeTab === "Completed" && (
                <div className="pl-12 mt-2">
                  <button
                    onClick={() => setExpandedOutcome(expandedOutcome === item.id ? null : item.id)}
                    className="flex items-center gap-1 text-[10.5px] font-semibold transition-colors"
                    style={{ color: C.blue }}
                  >
                    Add outcome note <ChevronDown size={11} className={`transition-transform ${expandedOutcome === item.id ? "rotate-180" : ""}`} />
                  </button>
                  {expandedOutcome === item.id && (
                    <textarea
                      className="mt-1.5 w-full rounded-lg border border-border text-[11.5px] p-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
                      rows={2}
                      placeholder="e.g. Grade improved to passing / Withdrew from course"
                    />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
