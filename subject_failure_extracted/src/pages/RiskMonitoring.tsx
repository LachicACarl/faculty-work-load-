import { useState } from "react";
import { TrendingUp, TrendingDown, ArrowRight, Filter } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { C, mono, SectionHeading, Card } from "../app/shared";

const factorsData = [
  { factor: "Low Quiz Scores", pct: 45, color: C.high },
  { factor: "Consecutive Absences", pct: 30, color: C.moderate },
  { factor: "Missed Deadlines", pct: 25, color: C.purple },
  { factor: "Low Lab Attendance", pct: 18, color: C.blue },
  { factor: "Late Submissions", pct: 14, color: "#0891b2" },
];

const cohortFactors = [
  { factor: "Avg. Quiz Score Drop", pct: 38, color: C.high },
  { factor: "Class Absence Rate", pct: 27, color: C.moderate },
  { factor: "Incomplete Lab Work", pct: 22, color: C.purple },
  { factor: "Missed Assessments", pct: 19, color: C.blue },
  { factor: "LMS Inactivity", pct: 11, color: "#0891b2" },
];

const chartData = [
  { name: "Low Quiz", individual: 45, cohort: 38 },
  { name: "Absences", individual: 30, cohort: 27 },
  { name: "Deadlines", individual: 25, cohort: 22 },
  { name: "Lab", individual: 18, cohort: 19 },
  { name: "Submissions", individual: 14, cohort: 11 },
];

type FeedItem = {
  student: string; initials: string;
  from: "Low" | "Moderate" | "High"; to: "Low" | "Moderate" | "High";
  subject: string; time: string; critical: boolean;
};

const feed: FeedItem[] = [
  { student: "Rafael Mendoza", initials: "RM", from: "Moderate", to: "High", subject: "Physics", time: "12m ago", critical: true },
  { student: "Marco Dela Cruz", initials: "MD", from: "Moderate", to: "High", subject: "Math", time: "43m ago", critical: true },
  { student: "Sofia Cruz", initials: "SC", from: "High", to: "Low", subject: "Prog. 2", time: "1h ago", critical: false },
  { student: "Andrea Lim", initials: "AL", from: "Low", to: "Moderate", subject: "Calc. 2", time: "2h ago", critical: false },
  { student: "Camille Torres", initials: "CT", from: "Moderate", to: "High", subject: "Discrete Math", time: "3h ago", critical: true },
  { student: "Paolo Bautista", initials: "PB", from: "Moderate", to: "Low", subject: "Math", time: "5h ago", critical: false },
  { student: "Maria Gonzales", initials: "MG", from: "Low", to: "Moderate", subject: "Physics", time: "6h ago", critical: false },
  { student: "Juan Santos", initials: "JS", from: "Moderate", to: "High", subject: "Prog. 2", time: "1d ago", critical: true },
];

const riskColor: Record<string, string> = { High: C.high, Moderate: C.moderate, Low: C.low };

export default function RiskMonitoring() {
  const [mode, setMode] = useState<"individual" | "cohort">("individual");
  const [onlyCritical, setOnlyCritical] = useState(false);

  const factors = mode === "individual" ? factorsData : cohortFactors;
  const visibleFeed = onlyCritical ? feed.filter((f) => f.critical) : feed;

  return (
    <div className="px-5 py-4 space-y-4">
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>

        {/* Left — Risk Factors Analysis */}
        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <SectionHeading>Risk Factors Analysis</SectionHeading>
            <div className="flex items-center gap-1 bg-[#edf0f7] rounded-lg p-0.5">
              {(["individual", "cohort"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className="px-3 py-1 rounded-md text-[11px] font-semibold transition-all capitalize"
                  style={mode === m ? { background: C.navy, color: "#fff" } : { color: "#64748b" }}
                >
                  {m === "individual" ? "Individual" : "Cohort"}
                </button>
              ))}
            </div>
          </div>

          {/* Bar chart */}
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 16, left: 60, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f3f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} domain={[0, 50]} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: "#64748b" }} tickLine={false} axisLine={false} width={56} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} formatter={(v) => [`${v}%`]} />
                <Bar dataKey={mode === "individual" ? "individual" : "cohort"} fill={C.blue} radius={[0, 4, 4, 0]} name={mode === "individual" ? "Individual %" : "Cohort %"} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Factor list */}
          <div className="space-y-2.5 mt-1">
            {factors.map((f) => (
              <div key={f.factor}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11.5px] font-medium" style={{ color: C.navy }}>{f.factor}</span>
                  <span className="text-[12px] font-bold" style={{ ...mono, color: f.color }}>{f.pct}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-[#edf0f7] overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${f.pct}%`, background: f.color }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Right — Risk Volatility Feed */}
        <Card className="flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <SectionHeading>Risk Volatility Feed</SectionHeading>
            <button
              onClick={() => setOnlyCritical(!onlyCritical)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-all border"
              style={onlyCritical
                ? { background: C.high, color: "#fff", borderColor: C.high }
                : { background: "transparent", color: "#64748b", borderColor: "#e2e8f0" }}
            >
              <Filter size={11} />
              Critical Only
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2" style={{ maxHeight: 460 }}>
            {visibleFeed.map((item, i) => {
              const escalated = ["Low", "Moderate", "High"].indexOf(item.to) > ["Low", "Moderate", "High"].indexOf(item.from);
              return (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-xl border transition-colors"
                  style={{ borderColor: item.critical ? `${C.high}30` : "#f0f3f9", background: item.critical ? `${C.high}06` : "#fafbfd" }}
                >
                  <div
                    className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white text-[10px] font-bold"
                    style={{ background: riskColor[item.to] }}
                  >
                    {item.initials}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12px] font-semibold" style={{ color: C.navy }}>{item.student}</p>
                    <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full" style={{ background: `${riskColor[item.from]}18`, color: riskColor[item.from] }}>{item.from}</span>
                      {escalated
                        ? <TrendingUp size={11} style={{ color: C.high }} />
                        : <TrendingDown size={11} style={{ color: C.low }} />}
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full" style={{ background: `${riskColor[item.to]}18`, color: riskColor[item.to] }}>{item.to}</span>
                      <span className="text-[10px] text-muted-foreground ml-1">in {item.subject}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="text-[9px] text-muted-foreground">{item.time}</span>
                    {item.critical && (
                      <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: `${C.high}18`, color: C.high }}>Critical</span>
                    )}
                  </div>
                </div>
              );
            })}
            {visibleFeed.length === 0 && (
              <p className="text-[12px] text-muted-foreground text-center py-8">No critical escalations at this time.</p>
            )}
          </div>

          <button className="mt-3 w-full py-1.5 rounded-lg border border-[#2563eb]/25 text-[11px] font-semibold text-[#2563eb] hover:bg-[#2563eb]/6 transition-colors">
            <span className="flex items-center justify-center gap-1.5">View Full Report <ArrowRight size={12} /></span>
          </button>
        </Card>
      </div>
    </div>
  );
}
