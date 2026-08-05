import React from "react";

/* ─── Palette ─── */
export const C = {
  slate: "#1e293b",
  teal: "#0d9488",
  sky: "#0ea5e9",
  amber: "#d97706",
  red: "#dc2626",
  green: "#16a34a",
  purple: "#7c3aed",
  bg: "#f0f4f8",
};

export const mono: React.CSSProperties = { fontFamily: "'DM Mono', monospace" };

/* ─── Shared UI atoms ─── */
export function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[9.5px] font-bold uppercase tracking-[0.14em] text-muted-foreground mb-3">
      {children}
    </p>
  );
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-black/7 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({ label, value, sub, color, icon }: {
  label: string; value: string | number; sub?: string; color: string; icon: React.ReactNode;
}) {
  return (
    <Card className="p-4 flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${color}18` }}>
        <span style={{ color }}>{icon}</span>
      </div>
      <div>
        <p className="text-[24px] font-bold leading-none" style={{ ...mono, color }}>{value}</p>
        <p className="text-[10.5px] font-semibold mt-0.5" style={{ color: C.slate }}>{label}</p>
        {sub && <p className="text-[10px] text-muted-foreground mt-0.5">{sub}</p>}
      </div>
    </Card>
  );
}

export type MatchLevel = "Exact" | "Partial" | "Unmatched";
export const matchColor: Record<MatchLevel, string> = {
  Exact: C.green, Partial: C.amber, Unmatched: C.red,
};

export function MatchBadge({ level }: { level: MatchLevel }) {
  const color = matchColor[level];
  return (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: `${color}18`, color }}>
      {level}
    </span>
  );
}

export type ApprovalStatus = "Pending" | "Approved" | "Flagged";
export const approvalColor: Record<ApprovalStatus, string> = {
  Approved: C.green, Pending: C.amber, Flagged: C.red,
};

export function StatusBadge({ status }: { status: ApprovalStatus }) {
  const color = approvalColor[status];
  return (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: `${color}18`, color }}>
      {status}
    </span>
  );
}
