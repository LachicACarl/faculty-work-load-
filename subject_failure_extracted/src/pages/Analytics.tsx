import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, LineChart, Line, BarChart, Bar, Legend,
} from "recharts";
import { C, mono, SectionHeading, Card } from "../app/shared";

const scatterData = [
  { lms: 2, exam: 48 }, { lms: 5, exam: 55 }, { lms: 8, exam: 62 },
  { lms: 12, exam: 70 }, { lms: 3, exam: 42 }, { lms: 15, exam: 78 },
  { lms: 10, exam: 68 }, { lms: 6, exam: 57 }, { lms: 18, exam: 82 },
  { lms: 1, exam: 39 }, { lms: 20, exam: 88 }, { lms: 9, exam: 65 },
  { lms: 4, exam: 51 }, { lms: 14, exam: 75 }, { lms: 7, exam: 60 },
  { lms: 16, exam: 80 }, { lms: 11, exam: 72 }, { lms: 13, exam: 74 },
];

const accuracyData = [
  { semester: "1st 2024", accuracy: 78, precision: 72 },
  { semester: "2nd 2024", accuracy: 82, precision: 79 },
  { semester: "1st 2025", accuracy: 85, precision: 83 },
  { semester: "2nd 2025", accuracy: 88, precision: 86 },
  { semester: "1st 2026", accuracy: 91, precision: 89 },
];

const cohortData = [
  { year: "AY 2023–24", high: 18, moderate: 22, low: 86 },
  { year: "AY 2024–25", high: 22, moderate: 24, low: 80 },
  { year: "AY 2025–26", high: 25, moderate: 26, low: 75 },
];

const subjectTrend = [
  { subject: "Math", "AY 23-24": 72, "AY 24-25": 78, "AY 25-26": 84 },
  { subject: "Physics", "AY 23-24": 68, "AY 24-25": 71, "AY 25-26": 69 },
  { subject: "Prog. 2", "AY 23-24": 75, "AY 24-25": 80, "AY 25-26": 77 },
  { subject: "Disc. Math", "AY 23-24": 65, "AY 24-25": 70, "AY 25-26": 73 },
  { subject: "Calc. 2", "AY 23-24": 61, "AY 24-25": 66, "AY 25-26": 64 },
];

const modelStats = [
  { label: "Prediction Accuracy", value: "91%", color: C.low },
  { label: "Precision Score", value: "89%", color: C.blue },
  { label: "Recall Rate", value: "87%", color: C.purple },
  { label: "F1 Score", value: "88%", color: C.moderate },
];

export default function Analytics() {
  return (
    <div className="px-5 py-4 space-y-4">

      {/* Model stats strip */}
      <div className="grid grid-cols-4 gap-3">
        {modelStats.map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-2xl border border-black/7 p-4 shadow-sm text-center">
            <p className="text-[28px] font-bold" style={{ ...mono, color }}>{value}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Top section */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>

        {/* Scatter: LMS logins vs exam scores */}
        <Card>
          <SectionHeading>LMS Activity vs Exam Performance</SectionHeading>
          <p className="text-[10px] text-muted-foreground mb-3 leading-snug">
            Correlation between weekly LMS login frequency and actual exam scores
          </p>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f3f9" />
                <XAxis
                  dataKey="lms" name="LMS Logins/Week" type="number"
                  tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }}
                  tickLine={false} axisLine={false} label={{ value: "LMS Logins/Week", position: "insideBottom", offset: -2, fontSize: 9, fill: "#94a3b8" }}
                />
                <YAxis
                  dataKey="exam" name="Exam Score" type="number" domain={[30, 100]}
                  tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }}
                  tickLine={false} axisLine={false}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }}
                  formatter={(v, name) => [name === "lms" ? `${v} logins/wk` : `${v} pts`, name === "lms" ? "LMS Activity" : "Exam Score"]}
                />
                <Scatter data={scatterData} fill={C.blue} fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Line: Model accuracy over semesters */}
        <Card>
          <SectionHeading>Prediction Accuracy Over Time</SectionHeading>
          <p className="text-[10px] text-muted-foreground mb-3 leading-snug">
            Historical accuracy of failure predictions vs. actual outcomes per semester
          </p>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={accuracyData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f3f9" />
                <XAxis dataKey="semester" tick={{ fontSize: 8, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} domain={[70, 100]} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} formatter={(v) => [`${v}%`]} />
                <Line type="monotone" dataKey="accuracy" stroke={C.blue} strokeWidth={2.5} dot={{ r: 4, fill: C.blue }} name="Accuracy" />
                <Line type="monotone" dataKey="precision" stroke={C.purple} strokeWidth={2} strokeDasharray="4 2" dot={{ r: 3, fill: C.purple }} name="Precision" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-2">
            {[["Accuracy", C.blue], ["Precision", C.purple]].map(([l, c]) => (
              <div key={l as string} className="flex items-center gap-1.5">
                <span className="block w-4 h-0.5 rounded-full" style={{ background: c as string }} />
                <span className="text-[9.5px] text-muted-foreground">{l}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Bottom section */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>

        {/* Cohort comparison */}
        <Card>
          <SectionHeading>Cohort Risk Distribution by Academic Year</SectionHeading>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cohortData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f3f9" vertical={false} />
                <XAxis dataKey="year" tick={{ fontSize: 9, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                <Bar dataKey="high" stackId="a" fill={C.high} name="High Risk" />
                <Bar dataKey="moderate" stackId="a" fill={C.moderate} name="Moderate Risk" />
                <Bar dataKey="low" stackId="a" fill={C.low} name="Low Risk" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-2">
            {[["High", C.high], ["Moderate", C.moderate], ["Low", C.low]].map(([l, c]) => (
              <div key={l as string} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ background: c as string }} />
                <span className="text-[9.5px] text-muted-foreground">{l} Risk</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Subject failure rates */}
        <Card>
          <SectionHeading>Subject Failure Rate Trends by Academic Year</SectionHeading>
          <div style={{ height: 200 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={subjectTrend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f3f9" />
                <XAxis dataKey="subject" tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 8.5, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} domain={[55, 90]} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} formatter={(v) => [`${v}%`]} />
                <Line type="monotone" dataKey="AY 23-24" stroke="#94a3b8" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="AY 24-25" stroke={C.blue} strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="AY 25-26" stroke={C.navy} strokeWidth={2.5} dot={{ r: 4, fill: C.navy }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-2">
            {[["AY 23-24", "#94a3b8"], ["AY 24-25", C.blue], ["AY 25-26 (current)", C.navy]].map(([l, c]) => (
              <div key={l as string} className="flex items-center gap-1.5">
                <span className="block w-4 h-0.5 rounded-full" style={{ background: c as string }} />
                <span className="text-[9.5px] text-muted-foreground">{l}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
