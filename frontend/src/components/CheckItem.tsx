"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { StatusPill } from "./StatusPill";
import type { CheckFinding } from "@/lib/api";

interface CheckItemProps {
  check: CheckFinding;
}

function oneLiner(check: CheckFinding): string {
  const { file } = check.evidence || { file: "—", snippet: "" };
  if (file && file !== "—") return `File: ${file}`;
  return check.recommendation;
}

export function CheckItem({ check }: CheckItemProps) {
  const [open, setOpen] = useState(false);
  const { file, snippet } = check.evidence || { file: "—", snippet: "" };
  const hasDetails = (file && file !== "—") || snippet || check.recommendation;

  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill status={check.status} />
          <span className="font-medium text-slate-900">{check.name}</span>
        </div>
        {hasDetails && (
          <button
            type="button"
            onClick={() => setOpen(!open)}
            className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
            aria-expanded={open}
          >
            {open ? (
              <ChevronDown className="h-4 w-4" aria-hidden />
            ) : (
              <ChevronRight className="h-4 w-4" aria-hidden />
            )}
            {open ? "Less" : "Evidence"}
          </button>
        )}
      </div>
      <p className="mt-1 text-sm text-slate-600">{oneLiner(check)}</p>
      <AnimatePresence>
        {open && hasDetails && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-2 border-t border-slate-200 pt-3">
              {(file && file !== "—") || snippet ? (
                <div>
                  <p className="mb-1 text-xs font-medium text-slate-500">
                    Evidence
                  </p>
                  {file && file !== "—" && (
                    <p className="text-xs text-slate-600">File: {file}</p>
                  )}
                  {snippet && (
                    <pre className="mt-1 max-h-32 overflow-auto rounded bg-slate-100 p-2 font-mono text-xs text-slate-700 whitespace-pre-wrap break-words">
                      {snippet}
                    </pre>
                  )}
                </div>
              ) : null}
              {check.recommendation && (
                <div>
                  <p className="mb-1 text-xs font-medium text-slate-500">
                    Recommendation
                  </p>
                  <p className="text-sm text-slate-700">
                    {check.recommendation}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
