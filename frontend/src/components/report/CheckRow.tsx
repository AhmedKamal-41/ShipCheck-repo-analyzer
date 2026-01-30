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
  const { file, snippet, start_line, end_line } = check.evidence ?? {
    file: "—",
    snippet: "",
  };
  const hasDetails =
    (file && file !== "—") || !!snippet || !!check.recommendation;
  const fileLabel =
    file && file !== "—"
      ? start_line != null && end_line != null
        ? `${file} (L${start_line}–${end_line})`
        : file
      : null;

  return (
    <div className="rounded-lg border border-[#d0d7de] bg-[#f6f8fa] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-3">
          <Badge status={check.status}>{check.status}</Badge>
          <span className="font-medium text-[#1f2328]">{check.name}</span>
        </div>
        {hasDetails && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-[#57606a] transition-colors hover:bg-[#f6f8fa] hover:text-[#1f2328]"
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
        <p className="mt-3 text-sm text-[#57606a] leading-relaxed">{check.recommendation}</p>
      )}
      {open && hasDetails && (
        <div className="mt-4 space-y-4 border-t border-[#d0d7de] pt-4">
          {((file && file !== "—") || snippet) && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#57606a]">
                Evidence
              </p>
              {fileLabel && (
                <p className="text-sm text-[#57606a]">
                  <span className="font-medium text-[#1f2328]">File:</span>{" "}
                  {fileLabel}
                </p>
              )}
              {snippet && (
                <pre className="mt-2 max-h-48 overflow-auto rounded-md border border-[#d0d7de] bg-[#f6f8fa] p-3 font-mono text-xs leading-relaxed text-[#1f2328] whitespace-pre-wrap break-words">
                  {snippet}
                </pre>
              )}
            </div>
          )}
          {check.recommendation && (
            <div className="border-t border-[#d0d7de] pt-4">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#57606a]">
                Recommendation
              </p>
              <p className="text-sm text-[#1f2328] leading-relaxed">{check.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
