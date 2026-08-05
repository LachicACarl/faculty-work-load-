import { useState } from "react";
import { User, Bell, Sliders, Users, Eye, EyeOff, Shield, Plus, Trash2 } from "lucide-react";
import { C, mono, SectionHeading } from "../app/shared";

type SubTab = "Profile" | "Notifications" | "Thresholds" | "User Management";

const SUB_TABS: { id: SubTab; icon: typeof User }[] = [
  { id: "Profile", icon: User },
  { id: "Notifications", icon: Bell },
  { id: "Thresholds", icon: Sliders },
  { id: "User Management", icon: Users },
];

const USERS = [
  { name: "Dr. Ana Reyes", email: "a.reyes@plm.edu.ph", role: "Department Head", subjects: ["Math", "Physics"] },
  { name: "Prof. Luis Dela Cruz", email: "l.delacruz@plm.edu.ph", role: "Faculty", subjects: ["Prog. 2", "Discrete Math"] },
  { name: "Ms. Clara Santos", email: "c.santos@plm.edu.ph", role: "Faculty", subjects: ["Calc. 2", "Math"] },
  { name: "Prof. Jose Garcia", email: "j.garcia@plm.edu.ph", role: "Faculty", subjects: ["Physics"] },
];

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="relative w-9 h-5 rounded-full transition-colors flex-shrink-0"
      style={{ background: checked ? C.blue : "#cbd5e1" }}
    >
      <span
        className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
        style={{ transform: checked ? "translateX(16px)" : "translateX(0)" }}
      />
    </button>
  );
}

function SliderInput({ label, value, onChange, min, max, color }: {
  label: string; value: number; onChange: (v: number) => void; min: number; max: number; color: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[12px] font-medium" style={{ color: C.navy }}>{label}</span>
        <span className="text-[13px] font-bold px-2 py-0.5 rounded-lg" style={{ ...mono, background: `${color}15`, color }}>{value}%</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{ accentColor: color }}
      />
      <div className="flex justify-between mt-0.5">
        <span className="text-[9px] text-muted-foreground" style={mono}>{min}%</span>
        <span className="text-[9px] text-muted-foreground" style={mono}>{max}%</span>
      </div>
    </div>
  );
}

export default function Settings() {
  const [tab, setTab] = useState<SubTab>("Profile");
  const [showPw, setShowPw] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Profile state
  const [name, setName] = useState("Administrator");
  const [email, setEmail] = useState("admin@plm.edu.ph");
  const [mfa, setMfa] = useState(true);

  // Notifications
  const [notifs, setNotifs] = useState({
    emailHighRisk: true, emailModerate: false, inAppHigh: true,
    inAppModerate: true, weeklyDigest: true, systemAlerts: true,
    threshold: 80,
  });

  // Thresholds
  const [highBound, setHighBound] = useState(75);
  const [modBound, setModBound] = useState(50);

  return (
    <div className="px-5 py-4">
      <div className="bg-white rounded-2xl border border-black/7 shadow-sm overflow-hidden">
        {/* Sub-navigation */}
        <div className="flex border-b border-border">
          {SUB_TABS.map(({ id, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className="flex-1 flex items-center justify-center gap-2 py-3 text-[12.5px] font-semibold transition-all border-b-2"
              style={{ borderColor: tab === id ? C.navy : "transparent", color: tab === id ? C.navy : "#64748b", background: tab === id ? "#f7f9fd" : "transparent" }}
            >
              <Icon size={14} />
              {id}
            </button>
          ))}
        </div>

        <div className="p-6 max-w-2xl">

          {/* ── Profile ── */}
          {tab === "Profile" && (
            <div className="space-y-5">
              <SectionHeading>Profile Settings</SectionHeading>
              <div className="flex items-center gap-4 mb-2">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-white text-[22px] font-bold" style={{ background: C.navy }}>A</div>
                <div>
                  <p className="text-[14px] font-bold" style={{ color: C.navy }}>{name}</p>
                  <p className="text-[12px] text-muted-foreground">{email}</p>
                  <button onClick={() => setMessage("Avatar change flow opened.")} className="text-[11px] font-semibold mt-1" style={{ color: C.blue }}>Change avatar</button>
                </div>
              </div>

              {[
                { label: "Full Name", value: name, set: setName, type: "text" },
                { label: "Email Address", value: email, set: setEmail, type: "email" },
              ].map(({ label, value, set, type }) => (
                <div key={label}>
                  <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">{label}</label>
                  <input
                    type={type}
                    value={value}
                    onChange={(e) => set(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-border text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              ))}

              <div>
                <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">New Password</label>
                <div className="relative">
                  <input
                    type={showPw ? "text" : "password"}
                    placeholder="Leave blank to keep current password"
                    className="w-full px-3 py-2 pr-10 rounded-xl border border-border text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 placeholder:text-muted-foreground/40"
                  />
                  <button onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl border border-border">
                <div className="flex items-center gap-3">
                  <Shield size={16} style={{ color: C.blue }} />
                  <div>
                    <p className="text-[12.5px] font-semibold" style={{ color: C.navy }}>Multi-Factor Authentication</p>
                    <p className="text-[10.5px] text-muted-foreground">Require 2FA for every login</p>
                  </div>
                </div>
                <Toggle checked={mfa} onChange={setMfa} />
              </div>

              <button onClick={() => setMessage("Profile saved locally.")} className="px-5 py-2 rounded-xl text-[13px] font-bold text-white" style={{ background: C.navy }}>
                Save Changes
              </button>
            </div>
          )}

          {/* ── Notifications ── */}
          {tab === "Notifications" && (
            <div className="space-y-5">
              <SectionHeading>Notification Preferences</SectionHeading>

              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-3">Email Alerts</p>
                <div className="space-y-3">
                  {[
                    { key: "emailHighRisk" as const, label: "Student escalates to High Risk", desc: "Immediate email when any student hits high risk" },
                    { key: "emailModerate" as const, label: "Student escalates to Moderate Risk", desc: "Immediate email for moderate risk escalations" },
                    { key: "weeklyDigest" as const, label: "Weekly Risk Digest", desc: "Summary email every Monday morning" },
                  ].map(({ key, label, desc }) => (
                    <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-[#f7f9fd]">
                      <div>
                        <p className="text-[12.5px] font-semibold" style={{ color: C.navy }}>{label}</p>
                        <p className="text-[10.5px] text-muted-foreground">{desc}</p>
                      </div>
                      <Toggle checked={notifs[key]} onChange={(v) => setNotifs({ ...notifs, [key]: v })} />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-3">In-App Alerts</p>
                <div className="space-y-3">
                  {[
                    { key: "inAppHigh" as const, label: "High Risk Notifications", desc: "Real-time banner alerts for high risk students" },
                    { key: "inAppModerate" as const, label: "Moderate Risk Notifications", desc: "In-app alerts for moderate escalations" },
                    { key: "systemAlerts" as const, label: "System Alerts", desc: "Model updates and maintenance notifications" },
                  ].map(({ key, label, desc }) => (
                    <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-[#f7f9fd]">
                      <div>
                        <p className="text-[12.5px] font-semibold" style={{ color: C.navy }}>{label}</p>
                        <p className="text-[10.5px] text-muted-foreground">{desc}</p>
                      </div>
                      <Toggle checked={notifs[key]} onChange={(v) => setNotifs({ ...notifs, [key]: v })} />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Alert Threshold — Failure Probability
                </label>
                <p className="text-[10.5px] text-muted-foreground mb-3">Send immediate alert when a student exceeds this probability</p>
                <SliderInput
                  label="Alert at probability above" value={notifs.threshold}
                  onChange={(v) => setNotifs({ ...notifs, threshold: v })}
                  min={50} max={95} color={C.high}
                />
              </div>

              <button onClick={() => setMessage("Notification preferences saved locally.")} className="px-5 py-2 rounded-xl text-[13px] font-bold text-white" style={{ background: C.navy }}>
                Save Preferences
              </button>
            </div>
          )}

          {/* ── Thresholds ── */}
          {tab === "Thresholds" && (
            <div className="space-y-5">
              <div className="flex items-center gap-2 mb-1">
                <SectionHeading>Risk Tier Configuration</SectionHeading>
                <span className="text-[9px] font-bold px-2 py-0.5 rounded-full mb-3" style={{ background: `${C.moderate}15`, color: C.moderate }}>Admin Only</span>
              </div>
              <p className="text-[12px] text-muted-foreground -mt-2">
                Adjust the probability thresholds that define each risk tier. Changes apply to all future predictions.
              </p>

              <div className="space-y-5">
                <SliderInput
                  label="High Risk threshold — above this value"
                  value={highBound} onChange={setHighBound}
                  min={60} max={90} color={C.high}
                />
                <SliderInput
                  label="Moderate Risk threshold — above this value"
                  value={modBound} onChange={setModBound}
                  min={30} max={highBound - 5} color={C.moderate}
                />
              </div>

              {/* Visual tier map */}
              <div className="rounded-xl border border-border p-4 space-y-2">
                <p className="text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">Current Tier Boundaries</p>
                {[
                  { label: "Low Risk", range: `0% – ${modBound - 1}%`, color: C.low },
                  { label: "Moderate Risk", range: `${modBound}% – ${highBound - 1}%`, color: C.moderate },
                  { label: "High Risk", range: `${highBound}% – 100%`, color: C.high },
                ].map(({ label, range, color }) => (
                  <div key={label} className="flex items-center justify-between p-2.5 rounded-lg" style={{ background: `${color}10` }}>
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                      <span className="text-[12px] font-semibold" style={{ color }}>{label}</span>
                    </div>
                    <span className="text-[12px] font-bold" style={{ ...mono, color }}>{range}</span>
                  </div>
                ))}
              </div>

              <button onClick={() => setMessage(`Thresholds updated: high ${highBound}%, moderate ${modBound}%.`)} className="px-5 py-2 rounded-xl text-[13px] font-bold text-white" style={{ background: C.navy }}>
                Apply Threshold Changes
              </button>
            </div>
          )}

          {/* ── User Management ── */}
          {tab === "User Management" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <SectionHeading>Faculty Members</SectionHeading>
                <button onClick={() => setMessage("Faculty creation flow opened.")} className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-bold text-white" style={{ background: C.blue }}>
                  <Plus size={13} /> Add Faculty
                </button>
              </div>

              <div className="space-y-2.5">
                {USERS.map((u) => (
                  <div key={u.email} className="flex items-center gap-3 p-3 rounded-xl border border-border hover:bg-[#f7f9fd] transition-colors">
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0" style={{ background: C.navy }}>
                      {u.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12.5px] font-semibold" style={{ color: C.navy }}>{u.name}</p>
                      <p className="text-[10.5px] text-muted-foreground">{u.email}</p>
                      <div className="flex gap-1 mt-1 flex-wrap">
                        <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-[#edf0f7] text-muted-foreground">{u.role}</span>
                        {u.subjects.map((s) => (
                          <span key={s} className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: `${C.blue}15`, color: C.blue }}>{s}</span>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      <button onClick={() => setMessage(`Edit flow opened for ${u.name}.`)} className="text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-border hover:bg-muted transition-colors text-muted-foreground">Edit</button>
                      <button onClick={() => setMessage(`${u.name} removed locally.`)} className="p-1.5 rounded-lg hover:bg-red-50 text-muted-foreground hover:text-red-500 transition-colors">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded-xl border border-border p-4 mt-4">
                <p className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-3">Access Audit Log</p>
                <div className="space-y-2">
                  {[
                    { user: "Admin", action: "Threshold configuration updated", time: "Jul 12 · 09:41 AM" },
                    { user: "Dr. Reyes", action: "Student profile viewed: 2021-00142", time: "Jul 12 · 08:55 AM" },
                    { user: "Prof. Garcia", action: "Intervention assigned: INT-004", time: "Jul 11 · 04:22 PM" },
                    { user: "Admin", action: "Monthly report generated", time: "Jul 11 · 10:00 AM" },
                  ].map((e, i) => (
                    <div key={i} className="flex items-center justify-between text-[11px]">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold" style={{ color: C.navy }}>{e.user}</span>
                        <span className="text-muted-foreground">{e.action}</span>
                      </div>
                      <span className="text-muted-foreground flex-shrink-0 ml-4" style={mono}>{e.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              {message && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-[12px] text-emerald-800">
                  {message}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
