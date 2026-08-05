import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router";
import {
  LayoutDashboard, Users, FlaskConical, ClipboardCheck,
  LogOut, Bell, ChevronDown, Cpu, BarChart3, FileText,
} from "lucide-react";
import { C } from "./shared";

const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", to: "/dashboard" },
  { icon: Users, label: "Faculty", to: "/dashboard/faculty" },
  { icon: FlaskConical, label: "Scenario Builder", to: "/dashboard/scenario-builder" },
  { icon: ClipboardCheck, label: "Allocation Review", to: "/dashboard/allocation-review" },
  { icon: BarChart3, label: "Analytics", to: "/dashboard/analytics" },
  { icon: FileText, label: "Reports", to: "/dashboard/reports" },
];

export default function Layout() {
  const [showLogout, setShowLogout] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="flex h-screen overflow-hidden" style={{ fontFamily: "'DM Sans', sans-serif", background: C.bg }}>

      {/* ══ Sidebar ══ */}
      <aside className="flex flex-col flex-shrink-0" style={{ width: 216, background: C.slate }}>
        {/* Brand */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: C.teal }}>
            <Cpu size={15} className="text-white" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/90 leading-tight">OFWAS</p>
            <p className="text-[9px] text-white/40 leading-tight mt-px">Workload Allocation</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 flex flex-col gap-px px-2.5 py-4">
          {NAV.map(({ icon: Icon, label, to }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] transition-all duration-150 w-full ${
                  isActive ? "text-white font-semibold" : "text-white/52 font-normal hover:bg-white/7 hover:text-white"
                }`
              }
              style={({ isActive }) => isActive ? { background: C.teal } : {}}
            >
              <Icon size={16} className="flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-2.5 pb-5">
          <button
            onClick={() => setShowLogout(true)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg w-full text-left text-[13px] text-white/35 hover:bg-white/7 hover:text-white transition-all"
          >
            <LogOut size={16} className="flex-shrink-0" />
            Logout
          </button>
        </div>
      </aside>

      {/* ══ Main ══ */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-2.5 bg-white border-b border-black/8 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <Cpu size={16} style={{ color: C.teal }} />
            <span className="text-[10.5px] font-bold uppercase tracking-wide" style={{ color: C.slate }}>
              Optimization-Based Faculty Workload Allocation System
            </span>
            <span className="text-[10.5px] text-muted-foreground">/ PLM Graduate School</span>
          </div>
          <div className="flex items-center gap-1.5">
            <button className="relative p-2 rounded-lg hover:bg-muted transition-colors">
              <Bell size={16} className="text-muted-foreground" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 ring-1 ring-white" />
            </button>
            <button className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-muted transition-colors">
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[9px] font-bold" style={{ background: C.slate }}>D</div>
              <span className="text-[12.5px] font-medium" style={{ color: C.slate }}>Dean Villanueva</span>
              <ChevronDown size={13} className="text-muted-foreground" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* ══ Logout Modal ══ */}
      {showLogout && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-[400px] border border-black/7">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${C.red}15` }}>
                <LogOut size={18} style={{ color: C.red }} />
              </div>
              <div>
                <h2 className="text-[15px] font-bold" style={{ color: C.slate }}>Confirm Logout</h2>
                <p className="text-[11px] text-muted-foreground">OFWAS — Workload Allocation System</p>
              </div>
            </div>
            <p className="text-[12.5px] text-muted-foreground leading-relaxed mb-5">
              Are you sure you want to log out? Any unsaved scenario configurations will be lost.
            </p>
            <div className="flex gap-2.5">
              <button onClick={() => setShowLogout(false)} className="flex-1 py-2 rounded-xl border border-border text-[13px] font-semibold text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
              <button onClick={() => { setShowLogout(false); navigate("/"); }} className="flex-1 py-2 rounded-xl text-[13px] font-semibold text-white transition-colors" style={{ background: C.slate }}>Yes, Log Out</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
