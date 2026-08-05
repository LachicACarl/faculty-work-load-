import { useState } from "react";
import { useNavigate } from "react-router";
import { Cpu, Eye, EyeOff, Lock, Mail } from "lucide-react";
import { C, mono } from "../app/shared";

const FEATURE_CHIPS = ["Genetic Algorithm", "Tabu Search", "Constraint Repair", "Explainable Scoring"];
const METRICS = [
  { value: "42", label: "Faculty Members" },
  { value: "87", label: "Sections to Fill" },
  { value: "91%", label: "Average Match" },
];

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
    <div className="min-h-screen lg:grid lg:grid-cols-[1.1fr_1fr]" style={{ fontFamily: "'DM Sans', sans-serif", background: "#edf2f9" }}>
      <style>{`
        @keyframes loginFadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatBlob {
          0% { transform: translateY(0) scale(1); }
          50% { transform: translateY(-18px) scale(1.04); }
          100% { transform: translateY(0) scale(1); }
        }
      `}</style>

      <section
        className="relative overflow-hidden p-8 sm:p-10 lg:p-12 xl:p-14 text-white"
        style={{
          background: "linear-gradient(135deg, #0f253f 0%, #182f4b 45%, #18455a 100%)",
          animation: "loginFadeUp .65s ease-out both",
        }}
      >
        <div
          className="pointer-events-none absolute -top-24 -right-20 h-96 w-96 rounded-full"
          style={{ background: "radial-gradient(circle at center, rgba(45, 212, 191, 0.26), rgba(45, 212, 191, 0.02) 72%)", animation: "floatBlob 9s ease-in-out infinite" }}
        />
        <div
          className="pointer-events-none absolute -bottom-24 -left-20 h-80 w-80 rounded-full"
          style={{ background: "radial-gradient(circle at center, rgba(14, 165, 233, 0.22), rgba(14, 165, 233, 0.02) 72%)", animation: "floatBlob 11s ease-in-out infinite" }}
        />
        <div
          className="pointer-events-none absolute inset-0 opacity-35"
          style={{
            backgroundImage: "linear-gradient(to right, rgba(255,255,255,0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.08) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            maskImage: "radial-gradient(circle at 45% 30%, black 35%, transparent 80%)",
          }}
        />

        <div className="relative z-10 flex h-full flex-col justify-between gap-10">
          <div style={{ animation: "loginFadeUp .6s ease-out .12s both" }}>
            <div className="mb-12 flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl" style={{ background: "rgba(22, 163, 74, 0.16)", border: "1px solid rgba(255,255,255,0.2)" }}>
                <Cpu size={20} className="text-white" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/90">OFWAS</p>
                <p className="text-[11px] text-white/55">PLM Graduate School</p>
              </div>
            </div>

            <p className="mb-3 inline-flex items-center rounded-full border border-white/20 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-white/75">
              Optimization Intelligence Portal
            </p>

            <h1 className="max-w-xl text-[34px] font-semibold leading-[1.08] sm:text-[44px]" style={{ fontFamily: "'Space Grotesk', 'DM Sans', sans-serif" }}>
              Reimagine Faculty Scheduling with Constraint-Aware Allocation
            </h1>

            <p className="mt-5 max-w-lg text-[15px] leading-relaxed text-white/70">
              OFWAS combines modified hybrid genetic optimization and tabu search to generate practical faculty loads with transparent conflict resolution.
            </p>

            <div className="mt-7 flex flex-wrap gap-2.5">
              {FEATURE_CHIPS.map((chip) => (
                <span
                  key={chip}
                  className="rounded-full border px-3 py-1.5 text-[11px] font-semibold"
                  style={{ borderColor: "rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.82)" }}
                >
                  {chip}
                </span>
              ))}
            </div>
          </div>

          <div style={{ animation: "loginFadeUp .6s ease-out .28s both" }}>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {METRICS.map(({ value, label }) => (
                <div key={label} className="rounded-2xl px-4 py-3" style={{ border: "1px solid rgba(255,255,255,0.13)", background: "rgba(255,255,255,0.07)" }}>
                  <p className="text-[27px] font-semibold text-white" style={mono}>{value}</p>
                  <p className="text-[11px] text-white/60">{label}</p>
                </div>
              ))}
            </div>

            <p className="mt-6 text-[11px] text-white/40">© 2026 PLM Graduate School - Department of Information Technology</p>
          </div>
        </div>
      </section>

      <section className="relative flex items-center justify-center px-5 py-10 sm:px-8 lg:px-10">
        <div className="w-full max-w-[460px]" style={{ animation: "loginFadeUp .7s ease-out .16s both" }}>
          <div className="mb-4 flex items-center gap-3 lg:hidden">
            <div className="grid h-10 w-10 place-items-center rounded-2xl text-white" style={{ background: C.slate }}>
              <Cpu size={17} />
            </div>
            <span className="text-sm font-semibold uppercase tracking-[0.16em]" style={{ color: C.slate }}>OFWAS Access</span>
          </div>

          <div className="rounded-3xl p-7 sm:p-8" style={{ background: "rgba(255,255,255,0.82)", backdropFilter: "blur(7px)", border: "1px solid rgba(30,41,59,0.1)", boxShadow: "0 25px 60px rgba(15, 23, 42, 0.13)" }}>
            <p className="mb-2 inline-block rounded-full bg-emerald-100 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-700">
              Secure Admin Access
            </p>
            <h2 className="text-[32px] font-semibold leading-none" style={{ color: C.slate, fontFamily: "'Space Grotesk', 'DM Sans', sans-serif" }}>Welcome Back</h2>
            <p className="mt-2 text-[14px] text-slate-500">Sign in to continue monitoring workload optimization runs.</p>

            <form onSubmit={handleSubmit} className="mt-7 space-y-4">
              <div>
                <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Email / Username</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="dean@plm.edu.ph"
                    required
                    className="w-full rounded-2xl border border-slate-200 bg-white/85 py-3 pr-4 pl-10 text-[14px] text-slate-700 transition-all focus:border-emerald-400 focus:outline-none focus:ring-4 focus:ring-emerald-100"
                  />
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">Password</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="........"
                    required
                    className="w-full rounded-2xl border border-slate-200 bg-white/85 py-3 pr-11 pl-10 text-[14px] text-slate-700 transition-all focus:border-emerald-400 focus:outline-none focus:ring-4 focus:ring-emerald-100"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-600"
                  >
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between gap-3 pt-1">
                <label className="flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                    className="h-4 w-4 rounded"
                    style={{ accentColor: C.teal }}
                  />
                  <span className="text-[13px] text-slate-500">Remember me</span>
                </label>
                <button type="button" className="text-[12.5px] font-semibold text-emerald-700 transition-colors hover:text-emerald-800">
                  Forgot Password?
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-1 w-full rounded-2xl py-3 text-[14px] font-semibold text-white transition-all disabled:cursor-not-allowed disabled:opacity-60"
                style={{ background: loading ? "#64748b" : "linear-gradient(110deg, #11263f 0%, #1b3858 100%)", boxShadow: loading ? "none" : "0 12px 26px rgba(17, 38, 63, 0.34)" }}
              >
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="mt-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="h-px flex-1 bg-slate-200" />
                <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">or</span>
                <div className="h-px flex-1 bg-slate-200" />
              </div>
              <button className="w-full rounded-2xl border border-slate-200 bg-white py-3 text-[14px] font-semibold text-slate-700 transition-colors hover:bg-slate-50">
                Continue with PLM University SSO
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
