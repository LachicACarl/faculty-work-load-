import { useState } from "react";
import { RefreshCw, Save, FlaskConical, CheckSquare, Square } from "lucide-react";
import { ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts";
import { C, mono, SectionHeading, Card } from "../app/shared";

interface Scenario {
  name: string;
  ftMax: number; ptMax: number; overload: number;
  specializationRequired: boolean; consecutiveLimit: number;
  balancePriority: number; utilizationTarget: number;
  fitnessScore: number; conflicts: number; avgMatch: number;
}

const DEFAULT: Scenario = {
  name: "Current Policy", ftMax: 21, ptMax: 12, overload: 3,
  specializationRequired: true, consecutiveLimit: 2,
  balancePriority: 70, utilizationTarget: 80,
  fitnessScore: 0.91, conflicts: 3, avgMatch: 88,
};

const SAVED_SCENARIOS: Scenario[] = [
  { ...DEFAULT, name: "Current Policy (Baseline)" },
  { ...DEFAULT, name: "High Utilization", ftMax: 24, ptMax: 15, overload: 6, utilizationTarget: 95, fitnessScore: 0.87, conflicts: 7, avgMatch: 79 },
  { ...DEFAULT, name: "Strict Specialization", specializationRequired: true, balancePriority: 90, fitnessScore: 0.94, conflicts: 1, avgMatch: 96 },
];

function PolicySlider({ label, value, onChange, min, max, unit = "", color }: {
  label: string; value: number; onChange: (v: number) => void; min: number; max: number; unit?: string; color?: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[12px] font-medium" style={{ color: C.slate }}>{label}</span>
        <span className="text-[13px] font-bold px-2 py-0.5 rounded-lg" style={{ ...mono, background: `${color ?? C.teal}15`, color: color ?? C.teal }}>
          {value}{unit}
        </span>
      </div>
      <input type="range" min={min} max={max} value={value} onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer" style={{ accentColor: color ?? C.teal }} />
      <div className="flex justify-between mt-0.5">
        <span className="text-[9px] text-muted-foreground" style={mono}>{min}{unit}</span>
        <span className="text-[9px] text-muted-foreground" style={mono}>{max}{unit}</span>
      </div>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!checked)}
      className="relative w-9 h-5 rounded-full transition-colors flex-shrink-0"
      style={{ background: checked ? C.teal : "#cbd5e1" }}>
      <span className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
        style={{ transform: checked ? "translateX(16px)" : "translateX(0)" }} />
    </button>
  );
}

export default function ScenarioBuilder() {
  const [scenario, setScenario] = useState<Scenario>({ ...DEFAULT, name: "My Scenario" });
  const [running, setRunning] = useState(false);
  const [simulated, setSimulated] = useState(false);
  const [savedList, setSavedList] = useState<Scenario[]>(SAVED_SCENARIOS);

  function set<K extends keyof Scenario>(k: K, v: Scenario[K]) {
    setScenario((s) => ({ ...s, [k]: v }));
    setSimulated(false);
  }

  function simulate() {
    setRunning(true);
    setTimeout(() => {
      const fit = Math.min(0.99, 0.72 + (scenario.specializationRequired ? 0.08 : 0) + (scenario.balancePriority / 1000) + Math.random() * 0.06);
      const conf = Math.max(0, 8 - Math.round(scenario.balancePriority / 20) + (scenario.specializationRequired ? -2 : 1));
      const match = Math.round(75 + (scenario.specializationRequired ? 12 : 0) + scenario.balancePriority / 10);
      setScenario((s) => ({ ...s, fitnessScore: +fit.toFixed(2), conflicts: conf, avgMatch: Math.min(99, match) }));
      setRunning(false);
      setSimulated(true);
    }, 1800);
  }

  function save() {
    setSavedList((prev) => [...prev.filter((s) => s.name !== scenario.name), { ...scenario }]);
  }

  const radarData = [
    { metric: "Utilization", value: scenario.utilizationTarget },
    { metric: "Specialization", value: scenario.specializationRequired ? 95 : 55 },
    { metric: "Balance", value: scenario.balancePriority },
    { metric: "Overload Flex", value: (scenario.overload / 9) * 100 },
    { metric: "Part-Time Use", value: (scenario.ptMax / 18) * 100 },
  ];

  const compareData = savedList.slice(-3).map((s) => ({ name: s.name.length > 16 ? s.name.slice(0, 14) + "…" : s.name, fitness: s.fitnessScore, conflicts: s.conflicts, match: s.avgMatch }));

  return (
    <div className="px-5 py-4 space-y-4">
      <div className="grid gap-4" style={{ gridTemplateColumns: "320px 1fr" }}>

        {/* Left — Policy Configuration */}
        <Card className="p-5 flex flex-col gap-4">
          <div>
            <SectionHeading>Scenario Name</SectionHeading>
            <input value={scenario.name} onChange={(e) => set("name", e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-border text-[13px] font-semibold focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              style={{ color: C.slate }} />
          </div>

          <div className="space-y-4">
            <SectionHeading>Workload Limits</SectionHeading>
            <PolicySlider label="Full-Time Max Units" value={scenario.ftMax} onChange={(v) => set("ftMax", v)} min={15} max={27} unit=" u" />
            <PolicySlider label="Part-Time Max Units" value={scenario.ptMax} onChange={(v) => set("ptMax", v)} min={6} max={18} unit=" u" />
            <PolicySlider label="Allowable Overload" value={scenario.overload} onChange={(v) => set("overload", v)} min={0} max={9} unit=" u" color={C.amber} />
          </div>

          <div className="space-y-3">
            <SectionHeading>Constraints</SectionHeading>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[12px] font-medium" style={{ color: C.slate }}>Require Specialization Match</p>
                <p className="text-[10px] text-muted-foreground">Only assign faculty within their declared specializations</p>
              </div>
              <Toggle checked={scenario.specializationRequired} onChange={(v) => set("specializationRequired", v)} />
            </div>
            <PolicySlider label="Max Consecutive Classes" value={scenario.consecutiveLimit} onChange={(v) => set("consecutiveLimit", v)} min={1} max={4} color={C.sky} />
          </div>

          <div className="space-y-4">
            <SectionHeading>Optimization Objectives</SectionHeading>
            <PolicySlider label="Balance Priority Weight" value={scenario.balancePriority} onChange={(v) => set("balancePriority", v)} min={0} max={100} unit="%" />
            <PolicySlider label="Utilization Target" value={scenario.utilizationTarget} onChange={(v) => set("utilizationTarget", v)} min={60} max={100} unit="%" color={C.green} />
          </div>

          <div className="flex gap-2 pt-2 border-t border-border">
            <button onClick={simulate} disabled={running}
              className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-[13px] font-bold text-white transition-all disabled:opacity-50"
              style={{ background: C.teal }}>
              <RefreshCw size={14} className={running ? "animate-spin" : ""} />
              {running ? "Simulating…" : "Run Simulation"}
            </button>
            <button onClick={save}
              className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl border border-border text-[12px] font-semibold text-muted-foreground hover:bg-muted transition-colors">
              <Save size={14} /> Save
            </button>
          </div>
        </Card>

        {/* Right — Results */}
        <div className="space-y-4">
          {/* Outcome metrics */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Fitness Score", value: simulated || !running ? scenario.fitnessScore : "…", color: scenario.fitnessScore >= 0.9 ? C.green : C.amber, fmt: (v: number | string) => typeof v === "number" ? v.toFixed(2) : v },
              { label: "Hard Conflicts", value: simulated || !running ? scenario.conflicts : "…", color: scenario.conflicts === 0 ? C.green : scenario.conflicts <= 3 ? C.amber : C.red, fmt: (v: number | string) => v },
              { label: "Avg Match Rate", value: simulated || !running ? `${scenario.avgMatch}%` : "…", color: (scenario.avgMatch ?? 0) >= 90 ? C.green : C.teal, fmt: (v: number | string) => v },
            ].map(({ label, value, color, fmt }) => (
              <Card key={label} className="p-4 text-center">
                <p className="text-[28px] font-bold" style={{ ...mono, color }}>{fmt(value)}</p>
                <p className="text-[10.5px] text-muted-foreground mt-0.5">{label}</p>
                {simulated && <p className="text-[9px] mt-1" style={{ color: C.teal }}>↑ Simulated result</p>}
              </Card>
            ))}
          </div>

          {/* Radar + compare */}
          <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <Card className="p-4">
              <SectionHeading>Policy Profile</SectionHeading>
              <div style={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9.5, fill: "#64748b" }} />
                    <Radar dataKey="value" stroke={C.teal} fill={C.teal} fillOpacity={0.18} strokeWidth={2} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} formatter={(v) => [`${v}%`]} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card className="p-4">
              <SectionHeading>Scenario Comparison</SectionHeading>
              <div style={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={compareData} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f8" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 8, fill: "#94a3b8" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 8, fill: "#94a3b8", fontFamily: "'DM Mono'" }} tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                    <Bar dataKey="match" fill={C.teal} name="Match %" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflicts" fill={C.amber} name="Conflicts" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* Saved scenarios */}
          <Card className="p-4">
            <SectionHeading>Saved Scenarios</SectionHeading>
            <div className="space-y-2">
              {savedList.map((s) => (
                <div key={s.name}
                  className="flex items-center gap-3 p-3 rounded-xl border border-border hover:bg-[#f7fafa] transition-colors cursor-pointer"
                  onClick={() => { setScenario({ ...s }); setSimulated(true); }}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${C.teal}15` }}>
                    <FlaskConical size={15} style={{ color: C.teal }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[12.5px] font-semibold" style={{ color: C.slate }}>{s.name}</p>
                    <p className="text-[10px] text-muted-foreground">
                      FT: {s.ftMax}u · PT: {s.ptMax}u · Fitness: <span style={mono}>{s.fitnessScore.toFixed(2)}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                      style={{ background: `${s.conflicts === 0 ? C.green : s.conflicts <= 3 ? C.amber : C.red}15`, color: s.conflicts === 0 ? C.green : s.conflicts <= 3 ? C.amber : C.red }}>
                      {s.conflicts} conflicts
                    </span>
                    {s.specializationRequired
                      ? <CheckSquare size={14} style={{ color: C.green }} />
                      : <Square size={14} className="text-muted-foreground" />}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
