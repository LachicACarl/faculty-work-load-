import { useState } from "react";
import { useNavigate } from "react-router";
import { Cpu, Eye, EyeOff, Lock, Mail } from "lucide-react";
import { C, mono } from "../app/shared";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => { setLoading(false); navigate("/dashboard"); }, 900);
  }

  return (
    <div className="min-h-screen flex" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-[46%] flex-col justify-between p-10 relative overflow-hidden" style={{ background: C.slate }}>
        <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full opacity-10" style={{ background: C.teal }} />
        <div className="absolute bottom-0 -left-16 w-72 h-72 rounded-full opacity-8" style={{ background: C.sky }} />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: C.teal }}>
              <Cpu size={20} className="text-white" />
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-widest text-white/80">OFWAS</p>
              <p className="text-[9px] text-white/40">PLM Graduate School</p>
            </div>
          </div>

          <h1 className="text-[30px] font-bold text-white leading-tight mb-4">
            Faculty Workload<br />Allocation System
          </h1>
          <p className="text-[13.5px] text-white/52 leading-relaxed max-w-xs">
            Powered by a Modified Hybrid Genetic and Tabu Search Algorithm for optimal, constraint-aware faculty scheduling.
          </p>

          {/* Algorithm badges */}
          <div className="flex flex-wrap gap-2 mt-6">
            {["Genetic Algorithm", "Tabu Search", "Constraint Repair", "Explainability"].map((t) => (
              <span key={t} className="text-[10px] font-semibold px-2.5 py-1 rounded-full" style={{ background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.6)" }}>{t}</span>
            ))}
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-3 gap-3">
          {[["42", "Faculty Members"], ["87", "Sections to Fill"], ["91%", "Avg Match Rate"]].map(([v, l]) => (
            <div key={l} className="rounded-xl p-3" style={{ background: "rgba(255,255,255,0.06)" }}>
              <p className="text-[22px] font-bold text-white" style={mono}>{v}</p>
              <p className="text-[10px] text-white/40 mt-0.5 leading-tight">{l}</p>
            </div>
          ))}
        </div>

        <p className="relative z-10 text-[10px] text-white/25">
          © 2026 PLM Graduate School – Dept. of Information Technology
        </p>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center px-6" style={{ background: C.bg }}>
        <div className="w-full max-w-[380px]">
          <div className="flex lg:hidden items-center gap-3 mb-8">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: C.slate }}>
              <Cpu size={17} className="text-white" />
            </div>
            <span className="text-[13px] font-bold uppercase tracking-wider" style={{ color: C.slate }}>OFWAS</span>
          </div>

          <h2 className="text-[24px] font-bold mb-1" style={{ color: C.slate }}>Welcome back</h2>
          <p className="text-[13px] text-muted-foreground mb-7">Sign in to your administrator account</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Email / Username</label>
              <div className="relative">
                <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="dean@plm.edu.ph" required
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-border bg-white text-[13px] focus:outline-none focus:ring-2 focus:ring-teal-500/25 focus:border-teal-400 transition-all" />
              </div>
            </div>

            <div>
              <label className="block text-[10.5px] font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input type={showPw ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••" required
                  className="w-full pl-9 pr-10 py-2.5 rounded-xl border border-border bg-white text-[13px] focus:outline-none focus:ring-2 focus:ring-teal-500/25 focus:border-teal-400 transition-all" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="w-3.5 h-3.5 rounded" style={{ accentColor: C.teal }} />
                <span className="text-[12px] text-muted-foreground">Remember me</span>
              </label>
              <button type="button" className="text-[12px] font-semibold hover:underline" style={{ color: C.teal }}>Forgot Password?</button>
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-xl text-[13px] font-bold text-white transition-all mt-1 disabled:opacity-60"
              style={{ background: loading ? "#64748b" : C.slate }}>
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <div className="mt-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-1 h-px bg-border" />
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">or</span>
              <div className="flex-1 h-px bg-border" />
            </div>
            <button className="w-full py-2.5 rounded-xl border border-border bg-white text-[13px] font-semibold text-foreground hover:bg-muted transition-colors">
              Continue with PLM University SSO
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
