"use client";

import { useState, useCallback } from "react";
import { Check, X, Copy } from "lucide-react";
import Link from "next/link";
import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";

const TABS = [
  "Overview",
  "Runability",
  "CI",
  "Security",
  "Interview Pack",
] as const;

function tabToSlug(tab: (typeof TABS)[number]): string {
  return tab.toLowerCase().replace(/\s+/g, "-");
}

type CheckItem = { status: "pass" | "fail"; title: string; note: string };

const OVERVIEW_CHECKS: CheckItem[] = [
  { status: "pass", title: "README install/run", note: "Found in README" },
  { status: "pass", title: "CI config", note: ".github/workflows" },
  { status: "pass", title: "Test directory", note: "tests/ present" },
  { status: "fail", title: "Dependency lockfile", note: "Add lockfile" },
];

const RUNABILITY_CHECKS: CheckItem[] = [
  { status: "pass", title: "README install/run", note: "Found in README" },
  { status: "pass", title: "Run script", note: "package.json scripts" },
  { status: "fail", title: "Entrypoints documented", note: "Add to README" },
];

const CI_CHECKS: CheckItem[] = [
  { status: "pass", title: "CI config", note: ".github/workflows" },
  { status: "pass", title: "Test directory", note: "tests/ present" },
  { status: "fail", title: "Test script", note: "Add to package.json" },
];

const SECURITY_CHECKS: CheckItem[] = [
  { status: "pass", title: "No secrets in repo", note: "Scan clean" },
  { status: "fail", title: "Dependency audit", note: "1 minor advisory" },
];

const TOP_ISSUES = [
  "Dependency lockfile missing",
  "No test script in package.json",
];

const NEXT_ACTIONS = [
  "Add a lockfile (package-lock.json or yarn.lock)",
  "Add test script to package.json",
  "Document run instructions in README",
];

const EVIDENCE_SNIPPET = `# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt`;

const INTERVIEW_QUESTIONS = [
  "How would you run this project locally?",
  "Where are tests and how do you run them?",
  "How does CI deploy or validate changes?",
];

function CheckList({ items, sectionLabel }: { items: CheckItem[]; sectionLabel: string }) {
  return (
    <div>
      <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
        {sectionLabel}
      </p>
      <ul className="space-y-0 divide-y divide-[var(--border)] rounded-lg border border-[var(--border)] overflow-hidden">
        {items.map((item) => (
          <li
            key={item.title}
            className="flex flex-wrap items-center gap-2 bg-[var(--surface-2)] px-3 py-2.5"
          >
            {item.status === "pass" ? (
              <Check className="h-4 w-4 shrink-0 text-[var(--success)]" />
            ) : (
              <X className="h-4 w-4 shrink-0 text-[var(--danger)]" />
            )}
            <span className="text-sm font-medium text-[var(--text)]">{item.title}</span>
            <span className="ml-auto text-xs text-[var(--muted)]">{item.note}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ExamplePreview() {
  const [activeTab, setActiveTab] = useState<(typeof TABS)[number]>("Overview");
  const toast = useToast();

  const handleCopySnippet = useCallback(() => {
    void navigator.clipboard.writeText(EVIDENCE_SNIPPET).then(() => toast.show("Copied"));
  }, [toast]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const idx = TABS.indexOf(activeTab);
      if (e.key === "ArrowRight" && idx < TABS.length - 1) {
        e.preventDefault();
        const next = TABS[idx + 1];
        setActiveTab(next);
        document.getElementById(`tab-${tabToSlug(next)}`)?.focus();
      } else if (e.key === "ArrowLeft" && idx > 0) {
        e.preventDefault();
        const prev = TABS[idx - 1];
        setActiveTab(prev);
        document.getElementById(`tab-${tabToSlug(prev)}`)?.focus();
      } else if (e.key === "Home") {
        e.preventDefault();
        setActiveTab(TABS[0]);
        document.getElementById(`tab-${tabToSlug(TABS[0])}`)?.focus();
      } else if (e.key === "End") {
        e.preventDefault();
        const last = TABS[TABS.length - 1];
        setActiveTab(last);
        document.getElementById(`tab-${tabToSlug(last)}`)?.focus();
      }
    },
    [activeTab]
  );

  return (
    <CenteredSection id="example" className="scroll-mt-20">
      <Container>
        <CenteredSectionHeader
          title="Example report"
          subtitle="A preview of what you get."
        />
        <div className="mx-auto max-w-6xl pt-6 md:pt-8">
          {/* App frame: outer wrapper with browser strip */}
          <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-2)] shadow-md">
            {/* Optional browser strip: 3 dots */}
            <div className="flex items-center gap-2 border-b border-[var(--border)] bg-[var(--surface-2)] px-4 py-2">
              <span className="h-2 w-2 rounded-full bg-[var(--border)]" aria-hidden />
              <span className="h-2 w-2 rounded-full bg-[var(--border)]" aria-hidden />
              <span className="h-2 w-2 rounded-full bg-[var(--border)]" aria-hidden />
            </div>
            <div className="rounded-b-2xl border-t-0 border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8">
              {/* Header bar: repo + pill (left), score + label (right) */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4">
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold text-[var(--text)]">
                    example-repo
                  </span>
                  <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--muted)]">
                    public
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-[var(--text)]">82</span>
                  <span className="text-sm text-[var(--muted)]">Readiness Score</span>
                </div>
              </div>

            {/* Status pills row */}
            <div className="mb-2 flex flex-wrap gap-2">
              <Badge status="pass">CI found</Badge>
              <Badge status="fail">Tests missing</Badge>
              <Badge status="pass">Docker ready</Badge>
            </div>

            {/* Metadata line */}
            <p className="mb-4 text-xs text-[var(--muted)]">
              Last scanned: 12s ago • Default branch: main • Detected: Next.js + FastAPI
            </p>

            {/* Tabs row: GitHub-style, accessible */}
            <div className="mb-6 border-b border-[var(--border)]" role="tablist">
              <div className="flex gap-0">
                {TABS.map((tab) => {
                  const slug = tabToSlug(tab);
                  return (
                    <button
                      key={tab}
                      id={`tab-${slug}`}
                      role="tab"
                      aria-selected={activeTab === tab}
                      aria-controls={`panel-${slug}`}
                      tabIndex={activeTab === tab ? 0 : -1}
                      type="button"
                      onClick={() => setActiveTab(tab)}
                      onKeyDown={handleKeyDown}
                      className={`-mb-px px-3 py-2 text-sm transition-colors ${
                        activeTab === tab
                          ? "border-b-2 border-[var(--link)] font-medium text-[var(--text)]"
                          : "border-b-2 border-transparent text-[var(--muted)] hover:text-[var(--text)] hover:underline"
                      }`}
                    >
                      {tab}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tab panels: only inner content switches */}
            {TABS.map((tab) => {
              const slug = tabToSlug(tab);
              const isActive = activeTab === tab;
              return (
                <div
                  key={tab}
                  id={`panel-${slug}`}
                  role="tabpanel"
                  aria-labelledby={`tab-${slug}`}
                  hidden={!isActive}
                >
                  {tab === "Overview" && (
                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.7fr_1fr]">
                      <div className="space-y-6">
                        <CheckList items={OVERVIEW_CHECKS} sectionLabel="Top checks" />
                        <div>
                          <div className="mb-2 flex items-center justify-between">
                            <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
                              Evidence snippet
                            </p>
                            <button
                              type="button"
                              onClick={handleCopySnippet}
                              title="Copy"
                              className="flex items-center gap-1 rounded p-1 text-[var(--muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30"
                              aria-label="Copy snippet"
                            >
                              <Copy className="h-3.5 w-3.5" />
                            </button>
                          </div>
                          <p className="mb-1 text-xs text-[var(--muted)]">Dockerfile</p>
                          <pre className="max-h-32 overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-3 font-mono text-sm leading-relaxed text-[var(--text)]">
                            {EVIDENCE_SNIPPET}
                          </pre>
                        </div>
                      </div>
                      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-4">
                        <div>
                          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
                            Top issues
                          </p>
                          <ul className="space-y-1.5">
                            {TOP_ISSUES.map((issue) => (
                              <li
                                key={issue}
                                className="flex items-center gap-2 text-sm text-[var(--text)]"
                              >
                                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--danger)]" />
                                {issue}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div className="mt-4">
                          <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
                            Next actions
                          </p>
                          <ol className="list-inside list-decimal space-y-1 text-xs text-[var(--text)]">
                            {NEXT_ACTIONS.map((action) => (
                              <li key={action}>{action}</li>
                            ))}
                          </ol>
                        </div>
                        <div className="mt-4 border-t border-[var(--border)] pt-3">
                          <p className="text-xs text-[var(--muted)]">
                            Suggested: GitHub Actions workflow
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {tab === "Runability" && (
                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.7fr_1fr]">
                      <div className="space-y-6">
                        <CheckList items={RUNABILITY_CHECKS} sectionLabel="Runability checks" />
                        <p className="text-sm text-[var(--muted)]">
                          Run instructions and entrypoints from README and config files.
                        </p>
                      </div>
                      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-4">
                        <p className="text-xs text-[var(--muted)]">
                          Focus: can a reviewer run and test this repo quickly?
                        </p>
                      </div>
                    </div>
                  )}

                  {tab === "CI" && (
                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.7fr_1fr]">
                      <div className="space-y-6">
                        <CheckList items={CI_CHECKS} sectionLabel="CI checks" />
                        <p className="text-sm text-[var(--muted)]">
                          Workflows and test scripts detected in the repo.
                        </p>
                      </div>
                      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-4">
                        <p className="text-xs text-[var(--muted)]">
                          Suggested: GitHub Actions workflow
                        </p>
                      </div>
                    </div>
                  )}

                  {tab === "Security" && (
                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.7fr_1fr]">
                      <div className="space-y-6">
                        <CheckList items={SECURITY_CHECKS} sectionLabel="Security signals" />
                        <p className="text-sm text-[var(--muted)]">
                          Secrets scan and dependency hygiene summary.
                        </p>
                      </div>
                      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-4">
                        <p className="text-xs text-[var(--muted)]">
                          No credentials or tokens in tracked files.
                        </p>
                      </div>
                    </div>
                  )}

                  {tab === "Interview Pack" && (
                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.7fr_1fr]">
                      <div className="space-y-4">
                        <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
                          Example interview questions
                        </p>
                        <ul className="space-y-2 text-sm text-[var(--text)]">
                          {INTERVIEW_QUESTIONS.map((q) => (
                            <li key={q} className="flex gap-2">
                              <span className="text-[var(--muted)]">•</span>
                              {q}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-4">
                        <p className="text-xs text-[var(--muted)]">
                          Coming next: full interview pack based on this repo.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* View full example button */}
            <div className="mt-8 flex justify-end">
              <Link
                href="#"
                className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface)] px-4 text-sm font-medium text-[var(--muted)] transition-colors hover:bg-[var(--surface-2)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30"
              >
                View full example
              </Link>
            </div>
            </div>
          </div>
        </div>
      </Container>
    </CenteredSection>
  );
}
