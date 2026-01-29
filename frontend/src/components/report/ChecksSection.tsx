"use client";

import type { SectionFinding, CheckFinding } from "@/lib/api";
import { CheckRow } from "./CheckRow";
import { Card } from "@/components/ui/Card";

interface ChecksSectionProps {
  section: SectionFinding;
  statusFilter: "all" | "fail" | "warn" | "pass";
  search: string;
  isInterviewPack?: boolean;
  questions?: string[];
}

function filterChecks(
  checks: CheckFinding[],
  statusFilter: "all" | "fail" | "warn" | "pass",
  search: string
): CheckFinding[] {
  let list = statusFilter === "all" ? checks : checks.filter((c) => c.status === statusFilter);
  const q = search.trim().toLowerCase();
  if (q) {
    list = list.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.recommendation ?? "").toLowerCase().includes(q) ||
        (c.evidence?.snippet ?? "").toLowerCase().includes(q) ||
        (c.evidence?.file ?? "").toLowerCase().includes(q)
    );
  }
  return list;
}

export function ChecksSection({
  section,
  statusFilter,
  search,
  isInterviewPack,
  questions = [],
}: ChecksSectionProps) {
  const filtered = isInterviewPack
    ? []
    : filterChecks(section.checks, statusFilter, search);
  const filteredQuestions = !isInterviewPack
    ? []
    : search.trim()
      ? questions.filter((line) =>
          line.toLowerCase().includes(search.trim().toLowerCase())
        )
      : questions;

  const count = isInterviewPack ? questions.length : section.checks.length;

  return (
    <Card className="hover:translate-y-0">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-heading text-lg font-semibold text-[#1f2328]">
          {section.name}
        </h3>
        <span className="rounded-lg border border-[#d0d7de] bg-[#f6f8fa] px-2.5 py-1 text-xs font-medium text-[#57606a]">
          {count} {isInterviewPack ? "question" : "check"}{count !== 1 ? "s" : ""}
        </span>
      </div>
      <div className="mt-5 space-y-3">
        {isInterviewPack ? (
          filteredQuestions.length === 0 ? (
            <p className="text-sm text-[#57606a]">No questions match the filter.</p>
          ) : (
            <ol className="list-inside list-decimal space-y-3 text-[#1f2328] leading-relaxed">
              {filteredQuestions.map((q, i) => (
                <li key={i} className="rounded-lg border border-[#d0d7de] bg-[#f6f8fa] p-3 text-sm">
                  {q}
                </li>
              ))}
            </ol>
          )
        ) : filtered.length === 0 ? (
          <p className="text-sm text-[#57606a]">No checks match the filter.</p>
        ) : (
          filtered.map((c) => <CheckRow key={c.id} check={c} />)
        )}
      </div>
    </Card>
  );
}
