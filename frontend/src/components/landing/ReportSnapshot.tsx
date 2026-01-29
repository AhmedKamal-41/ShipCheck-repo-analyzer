"use client";

import { Check, X } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

const SNAPSHOT_ROWS = [
  { status: "pass" as const, label: "README" },
  { status: "pass" as const, label: "CI" },
  { status: "fail" as const, label: "Tests" },
] as const;

export function ReportSnapshot() {
  return (
    <>
      {/* Desktop: compact panel */}
      <div className="hidden w-full max-w-xs rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow)] lg:block">
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          Example snapshot
        </p>
        <div className="mb-3 flex items-center gap-2">
          <span className="text-xl font-bold text-[var(--text)]">82</span>
          <span className="text-sm text-[var(--muted)]">Readiness Score</span>
        </div>
        <ul className="mb-3 space-y-1">
          {SNAPSHOT_ROWS.map((row) => (
            <li
              key={row.label}
              className="flex items-center gap-2 text-xs"
            >
              {row.status === "pass" ? (
                <Check className="h-3.5 w-3.5 shrink-0 text-[var(--success)]" />
              ) : (
                <X className="h-3.5 w-3.5 shrink-0 text-[var(--danger)]" />
              )}
              <span className="text-[var(--text)]">{row.label}</span>
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap gap-1.5">
          <Badge status="pass">CI found</Badge>
          <Badge status="fail">Tests missing</Badge>
          <Badge status="pass">Docker ready</Badge>
        </div>
      </div>

      {/* Mobile: horizontal strip */}
      <p className="mt-4 text-center text-xs text-[var(--muted)] lg:hidden">
        82 Readiness • CI ✓ • Tests ✗ • Docker ✓
      </p>
    </>
  );
}
