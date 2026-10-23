import { useState, type FormEvent } from "react";
import { Cpu, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { C } from "../app/shared";

export default function Login() {
  const [identity, setIdentity] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [feedback, setFeedback] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPassword("");
    setFeedback(
      "Authentication is not configured. OFWAS did not send or verify these credentials. Do not enter your real password on this preview page."
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-2">
      <section
        aria-label="OFWAS introduction"
        className="relative flex min-h-[250px] flex-col justify-between overflow-hidden px-7 py-8 text-white sm:px-12 sm:py-10 lg:min-h-screen lg:px-16 lg:py-14"
        style={{ background: C.slate }}
      >
        <div
          aria-hidden="true"
          className="absolute -right-28 -top-28 h-80 w-80 rounded-full border-[48px] border-white/5"
        />
        <div
          aria-hidden="true"
          className="absolute -bottom-36 -left-24 h-80 w-80 rounded-full bg-teal-500/10 blur-2xl"
        />

        <div className="relative z-10 flex items-center gap-3">
          <span
            className="flex h-11 w-11 items-center justify-center rounded-xl"
            style={{ background: C.teal }}
          >
            <Cpu size={21} aria-hidden="true" />
          </span>
          <span>
            <span className="block text-sm font-bold tracking-[0.18em]">OFWAS</span>
            <span className="mt-0.5 block text-xs text-white/65">PLM Graduate School</span>
          </span>
        </div>

        <div className="relative z-10 my-12 max-w-xl lg:my-auto lg:py-20">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-teal-300">
            Faculty Workload Allocation System
          </p>
          <h1 className="max-w-lg text-3xl font-semibold leading-tight sm:text-4xl lg:text-5xl">
            Workload planning with a clearer view.
          </h1>
          <p className="mt-5 max-w-md text-sm leading-7 text-white/65 sm:text-base">
            Review faculty, curriculum, and workload information in one workspace.
          </p>
        </div>

        <p className="relative z-10 text-xs text-white/45">
          Local development interface
        </p>
      </section>

      <section className="flex items-center justify-center px-5 py-10 sm:px-10 lg:px-14">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">
              PLM Graduate School
            </p>
          </div>

          <p className="text-sm font-semibold" style={{ color: C.teal }}>
            Welcome to OFWAS
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Sign in
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Use your institutional account when authentication becomes available.
          </p>

          <div
            role="note"
            className="mt-6 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm leading-6 text-amber-950"
          >
            Authentication is not configured. This is a UI preview; do not enter a real password. The dashboard and API are not protected by this page.
          </div>

          {feedback && (
            <p
              role="alert"
              aria-live="assertive"
              className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-800"
            >
              {feedback}
            </p>
          )}

          <form onSubmit={handleSubmit} className="mt-7 space-y-5">
            <div>
              <label
                htmlFor="ofwas-identity"
                className="mb-2 block text-sm font-medium text-slate-800"
              >
                Email or username
              </label>
              <div className="relative">
                <Mail
                  aria-hidden="true"
                  size={18}
                  className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  id="ofwas-identity"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={identity}
                  onChange={(event) => setIdentity(event.target.value)}
                  placeholder="name@institution.edu"
                  className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-400 focus:border-teal-600 focus:ring-4 focus:ring-teal-600/10"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="ofwas-password"
                className="mb-2 block text-sm font-medium text-slate-800"
              >
                Password
              </label>
              <div className="relative">
                <LockKeyhole
                  aria-hidden="true"
                  size={18}
                  className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  id="ofwas-password"
                  name="password"
                  type={passwordVisible ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Enter password"
                  className="w-full rounded-xl border border-slate-300 bg-white py-3 pl-11 pr-12 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 hover:border-slate-400 focus:border-teal-600 focus:ring-4 focus:ring-teal-600/10"
                />
                <button
                  type="button"
                  onClick={() => setPasswordVisible((visible) => !visible)}
                  aria-label={passwordVisible ? "Hide password" : "Show password"}
                  aria-pressed={passwordVisible}
                  className="absolute right-2.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"
                >
                  {passwordVisible ? (
                    <EyeOff size={18} aria-hidden="true" />
                  ) : (
                    <Eye size={18} aria-hidden="true" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full rounded-xl px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-700/25"
              style={{ background: C.slate }}
            >
              Sign in
            </button>
          </form>

          <p className="mt-6 text-center text-xs leading-5 text-slate-500">
            Sign-in is unavailable until an approved authentication service is connected. This page does not send credentials to a server or authenticate users.
          </p>
        </div>
      </section>
    </main>
  );
}
