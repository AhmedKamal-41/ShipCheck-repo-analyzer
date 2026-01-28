"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { CheckFinding } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";

interface CheckRowProps {
  check: CheckFinding;
}

export function CheckRow({ check }: CheckRowProps) {
  const [open, setOpen] = useState(false);
  const { file, snippet } = check.evidence ?? { file: "—", snippet: "" };
  const hasDetails =
    (file && file !== "—") || !!snippet || !!check.recommendation;

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <Badge status={check.status}>{check.status}</Badge>
          <span className="font-medium text-slate-900">{check.name}</span>
        </div>
        {hasDetails && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
            aria-expanded={open}
          >
            {open ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            {open ? "Less" : "Details"}
          </button>
        )}
      </div>
      {check.recommendation && !open && (
        <p className="mt-3 text-sm text-slate-600 leading-relaxed">{check.recommendation}</p>
      )}
      {open && hasDetails && (
        <div className="mt-4 space-y-4 border-t border-slate-200 pt-4">
          {((file && file !== "—") || snippet) && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
                Evidence
              </p>
              {file && file !== "—" && (
                <p className="text-sm text-slate-600">
                  <span className="font-medium text-slate-700">File:</span> {file}
                </p>
              )}
              {snippet && (
                <pre className="mt-2 max-h-48 overflow-auto rounded-lg border border-slate-200 bg-slate-100/80 p-4 font-mono text-xs leading-relaxed text-slate-700 whitespace-pre-wrap break-words">
                  {snippet}
                </pre>
              )}
            </div>
          )}
          {check.recommendation && (
            <div className="border-t border-slate-200 pt-4">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
                Recommendation
              </p>
              <p className="text-sm text-slate-700 leading-relaxed">{check.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
