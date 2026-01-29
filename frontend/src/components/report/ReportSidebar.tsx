"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { HighlightItem } from "./ScoreSummary";

function scoreColor(score: number) {
  if (score >= 70) return "text-[#1f883d]";
  if (score >= 40) return "text-[#9a6700]";
  return "text-[#cf222e]";
}

function scoreStroke(score: number) {
  if (score >= 70) return "stroke-[#1f883d]";
  if (score >= 40) return "stroke-[#9a6700]";
  return "stroke-[#cf222e]";
}

interface ReportSidebarProps {
  score: number;
  lastAnalyzed?: string;
  commitSha?: string | null;
  highlights: HighlightItem[];
  topIssues: { name: string; status: "fail" | "warn" }[];
  nextActions: string[];
}

export function ReportSidebar({
  score,
  lastAnalyzed,
  commitSha,
  highlights,
  topIssues,
  nextActions,
}: ReportSidebarProps) {
  const clamped = Math.min(100, Math.max(0, score));
  const r = 26;
  const dashArray = 2 * Math.PI * r;
  const dashOffset = dashArray - (clamped / 100) * dashArray;

  return (
    <aside className="space-y-4">
      <Card className="p-4">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#57606a]">
          Score
        </p>
        <div className="flex items-center gap-4">
          <div className="relative flex h-16 w-16 shrink-0 items-center justify-center">
            <svg
              className="-rotate-90"
              width={64}
              height={64}
              viewBox="0 0 64 64"
              aria-hidden
            >
              <circle
                cx="32"
                cy="32"
                r={26}
                fill="none"
                stroke="#d0d7de"
                strokeWidth="6"
              />
              <circle
                cx="32"
                cy="32"
                r={r}
                fill="none"
                strokeWidth="6"
                strokeLinecap="round"
                className={scoreStroke(score)}
                style={{
                  strokeDasharray: dashArray,
                  strokeDashoffset: dashOffset,
                }}
              />
            </svg>
            <span
              className={`font-heading absolute text-lg font-bold ${scoreColor(score)}`}
            >
              {score}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-[#1f2328]">Readiness</p>
            {lastAnalyzed && (
              <p className="mt-0.5 text-xs text-[#57606a]">{lastAnalyzed}</p>
            )}
            {commitSha && (
              <code className="mt-1 inline-block rounded border border-[#d0d7de] bg-[#f6f8fa] px-1.5 py-0.5 font-mono text-xs text-[#57606a]">
                {commitSha.slice(0, 7)}
              </code>
            )}
          </div>
        </div>
      </Card>

      <Card className="p-4">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#57606a]">
          Summary
        </p>
        <div className="flex flex-wrap gap-1.5">
          {highlights.map((h) => (
            <Badge key={h.label} status={h.status}>
              {h.label}
            </Badge>
          ))}
        </div>
      </Card>

      {topIssues.length > 0 && (
        <Card className="p-4">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#57606a]">
            Top issues
          </p>
          <ul className="space-y-2">
            {topIssues.map((issue) => (
              <li key={issue.name}>
                <Badge status={issue.status}>{issue.name}</Badge>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {nextActions.length > 0 && (
        <Card className="p-4">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#57606a]">
            Next actions
          </p>
          <ol className="list-inside list-decimal space-y-1 text-xs text-[#1f2328]">
            {nextActions.map((action, i) => (
              <li key={i}>{action}</li>
            ))}
          </ol>
        </Card>
      )}
    </aside>
  );
}
