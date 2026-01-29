"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Search } from "lucide-react";
import {
  type CheckFinding,
  type Report,
  type SectionFinding,
  analyzeRepo,
  getReport,
  isFindingsFailed,
  isFindingsSuccess,
} from "@/lib/api";
import type { HighlightItem } from "@/components/report/ScoreSummary";
import type { ReportTabId } from "@/components/report/ReportTabs";
import { Page } from "@/components/layout/Page";
import { Navbar } from "@/components/layout/Navbar";
import { Container } from "@/components/layout/Container";
import { Card } from "@/components/ui/Card";
import { ReportHeader } from "@/components/report/ReportHeader";
import { ReportTabs } from "@/components/report/ReportTabs";
import { ReportSidebar } from "@/components/report/ReportSidebar";
import { ChecksSection } from "@/components/report/ChecksSection";
import { ReportSkeleton } from "@/components/report/ReportSkeleton";
import { ReportError } from "@/components/report/ReportError";

const POLL_INTERVAL_MS = 2000;
const POLL_DEADLINE_MS = 30000;

/** Backend section name -> report tab id */
const SECTION_TO_TAB: Record<string, ReportTabId> = {
  Runability: "checks",
  Documentation: "checks",
  "Secrets Safety": "security",
  "Engineering Quality": "cicd",
  "Interview Pack": "interview-pack",
};

function mapSectionToTab(s: SectionFinding): ReportTabId {
  return SECTION_TO_TAB[s.name] ?? "checks";
}

function computeHighlights(
  sections: SectionFinding[],
  limit = 6
): HighlightItem[] {
  const fail: CheckFinding[] = [];
  const warn: CheckFinding[] = [];
  const pass: CheckFinding[] = [];
  for (const sec of sections) {
    for (const c of sec.checks) {
      if (c.status === "fail") fail.push(c);
      else if (c.status === "warn") warn.push(c);
      else pass.push(c);
    }
  }
  const ordered = [...fail, ...warn, ...pass];
  const out: HighlightItem[] = [];
  for (let i = 0; i < ordered.length && out.length < limit; i++) {
    const c = ordered[i];
    const label =
      c.status === "pass"
        ? `${c.name} detected`
        : c.status === "fail"
          ? `${c.name} missing`
          : `${c.name} (review)`;
    out.push({ label, status: c.status });
  }
  return out;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return "—";
  }
}

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const [report, setReport] = useState<Report | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [pollTimedOut, setPollTimedOut] = useState(false);
  const [activeTab, setActiveTab] = useState<ReportTabId>("overview");
  const [statusFilter, setStatusFilter] = useState<"all" | "fail" | "warn" | "pass">("all");
  const [search, setSearch] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const idRef = useRef(id);
  const mainRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (idRef.current !== id) {
      idRef.current = id;
      setPollTimedOut(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    getReport(id)
      .then((r) => {
        setReport(r);
        setErr(null);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Failed to load"));
  }, [id]);

  useEffect(() => {
    if (!id || report?.status !== "pending") return;
    const start = Date.now();
    intervalRef.current = setInterval(() => {
      if (Date.now() - start >= POLL_DEADLINE_MS) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
        setPollTimedOut(true);
        return;
      }
      getReport(id)
        .then((r) => {
          setReport(r);
          if (r.status !== "pending") {
            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        })
        .catch((e) => {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
          setErr(e instanceof Error ? e.message : "Failed to load");
        });
    }, POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [id, report?.status]);

  const handleTabChange = useCallback((tabId: ReportTabId) => {
    setActiveTab(tabId);
    if (tabId === "overview") {
      mainRef.current?.scrollIntoView({ behavior: "smooth" });
      return;
    }
    const el = document.getElementById(`section-${tabId}`);
    el?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const copyShareLink = useCallback(() => {
    if (typeof window === "undefined" || !navigator.clipboard?.writeText) return;
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {});
  }, []);

  const handleReanalyze = useCallback(() => {
    if (!report?.repo_url || retrying) return;
    setRetryError(null);
    setRetrying(true);
    analyzeRepo(report.repo_url)
      .then((data) => router.push(`/reports/${data.report_id}`))
      .catch((e) => {
        setRetryError(e instanceof Error ? e.message : "Re-analyze failed");
        setRetrying(false);
      });
  }, [report, retrying, router]);

  const isDone = report?.status === "done";
  const isFailed = report?.status === "failed";
  const isPending = report?.status === "pending";
  const findings = report?.findings_json ?? null;
  const successFindings = isFindingsSuccess(findings) ? findings : null;
  const failedFindings = isFindingsFailed(findings) ? findings : null;
  const sections = useMemo<SectionFinding[]>(
    () => (successFindings?.sections ?? []),
    [successFindings]
  );
  const score = successFindings?.overall_score ?? report?.overall_score ?? null;
  const errorMessage = failedFindings?.error ?? null;
  const interviewPack = useMemo(
    () => successFindings?.interview_pack ?? [],
    [successFindings]
  );

  const repoLabel =
    report?.repo_owner && report?.repo_name
      ? `${report.repo_owner}/${report.repo_name}`
      : report?.repo_url ?? "—";

  const highlights = useMemo(() => computeHighlights(sections, 6), [sections]);

  const sectionsByTab = useMemo(() => {
    const m: Record<ReportTabId, SectionFinding[]> = {
      overview: [],
      checks: [],
      security: [],
      cicd: [],
      "interview-pack": [],
    };
    for (const s of sections) {
      const tab = mapSectionToTab(s);
      if (tab === "interview-pack") {
        m["interview-pack"].push(s);
      } else {
        m[tab].push(s);
      }
    }
    return m;
  }, [sections]);

  const topIssues = useMemo(() => {
    const out: { name: string; status: "fail" | "warn" }[] = [];
    for (const sec of sections) {
      for (const c of sec.checks) {
        if ((c.status === "fail" || c.status === "warn") && out.length < 3) {
          out.push({ name: c.name, status: c.status });
        }
      }
    }
    return out;
  }, [sections]);

  const nextActions = useMemo(() => {
    const out: string[] = [];
    for (const sec of sections) {
      for (const c of sec.checks) {
        if (c.status === "fail" && c.recommendation && out.length < 5) {
          out.push(c.recommendation);
        }
      }
    }
    return out;
  }, [sections]);

  if (err) {
    return (
      <Page>
        <Navbar showTryCta={false} />
        <Container className="py-12 lg:py-16">
          <div className="mx-auto max-w-md rounded-lg border border-[#ffcecb] bg-[#ffebe9] p-6 text-center">
            <p className="text-sm font-medium text-[#cf222e]" role="alert">{err}</p>
            <Link
              href="/"
              className="mt-4 inline-block text-xs font-medium text-[#0969da] underline hover:text-[#085ec7]"
            >
              Back to home
            </Link>
          </div>
        </Container>
      </Page>
    );
  }

  if (!report) {
    return (
      <Page>
        <Navbar showTryCta={false} />
        <Container className="py-12 lg:py-16">
          <div className="flex flex-col items-center justify-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#d0d7de] border-t-[#0969da]" />
            <div className="text-center">
              <p className="text-sm font-medium text-[#1f2328]">Loading report…</p>
              <p className="text-xs text-[#57606a]">Please wait a moment.</p>
            </div>
          </div>
        </Container>
      </Page>
    );
  }

  return (
    <Page>
      <Navbar showTryCta={false} />
      <ReportHeader
        repoLabel={repoLabel}
        repoUrl={report.repo_url}
        copied={copied}
        retrying={retrying}
        onCopyLink={copyShareLink}
        onReanalyze={handleReanalyze}
      />

      {isPending && (
        <>
          {pollTimedOut && (
            <Container className="py-3">
              <p className="text-center text-xs text-[#57606a]">
                Still pending. Check back later or refresh.
              </p>
            </Container>
          )}
          <ReportSkeleton />
        </>
      )}

      {isFailed && (
        <>
          <ReportTabs activeId="overview" onChange={() => {}} />
          <Container className="py-4">
            <div ref={mainRef} className="flex gap-6 lg:gap-8">
              <div className="min-w-0 flex-1">
                <ReportError
                  message={errorMessage ?? "Analysis failed"}
                  retrying={retrying}
                  onRetry={handleReanalyze}
                  retryError={retryError}
                />
              </div>
              <div className="hidden w-72 shrink-0 lg:block">
                <div className="text-xs text-[#57606a]">—</div>
              </div>
            </div>
          </Container>
        </>
      )}

      {isDone && (
        <>
          <ReportTabs activeId={activeTab} onChange={handleTabChange} />
          <Container className="py-4 pb-16">
            <div className="flex gap-6 lg:gap-8">
              <div ref={mainRef} className="min-w-0 flex-1">
                <div className="mb-4 rounded-md border border-[#d0d7de] bg-white px-3 py-2">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap gap-2">
                      {(["all", "fail", "warn", "pass"] as const).map((s) => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => setStatusFilter(s)}
                          className={`rounded-md border px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                            statusFilter === s
                              ? "border-[#d0d7de] bg-[#f6f8fa] text-[#1f2328]"
                              : "border-[#d0d7de] bg-white text-[#57606a] hover:bg-[#f6f8fa]"
                          }`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                    <div className="relative w-full sm:w-56">
                      <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#57606a]" />
                      <input
                        type="search"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Filter checks…"
                        className="w-full rounded-md border border-[#d0d7de] bg-white py-1.5 pl-8 pr-2 text-sm text-[#1f2328] placeholder-[#57606a] focus:border-[#0969da] focus:outline-none focus:ring-1 focus:ring-[#0969da]"
                        aria-label="Filter checks or questions"
                      />
                    </div>
                  </div>
                </div>
                <div className="space-y-6">
                  <section id="section-checks" className="scroll-mt-24">
                    {sectionsByTab.checks.map((sec) => (
                      <ChecksSection
                        key={sec.name}
                        section={sec}
                        statusFilter={statusFilter}
                        search={search}
                      />
                    ))}
                    {sectionsByTab.checks.length === 0 && (
                      <Card>
                        <p className="text-sm text-[#57606a]">No checks data.</p>
                      </Card>
                    )}
                  </section>
                  <section id="section-security" className="scroll-mt-24">
                    {sectionsByTab.security.map((sec) => (
                      <ChecksSection
                        key={sec.name}
                        section={sec}
                        statusFilter={statusFilter}
                        search={search}
                      />
                    ))}
                    {sectionsByTab.security.length === 0 && (
                      <Card>
                        <p className="text-sm text-[#57606a]">No security data.</p>
                      </Card>
                    )}
                  </section>
                  <section id="section-cicd" className="scroll-mt-24">
                    {sectionsByTab.cicd.map((sec) => (
                      <ChecksSection
                        key={sec.name}
                        section={sec}
                        statusFilter={statusFilter}
                        search={search}
                      />
                    ))}
                    {sectionsByTab.cicd.length === 0 && (
                      <Card>
                        <p className="text-sm text-[#57606a]">No CI/CD data.</p>
                      </Card>
                    )}
                  </section>
                  <section id="section-interview-pack" className="scroll-mt-24">
                    <ChecksSection
                      section={{
                        name: "Interview Pack",
                        checks: [],
                        score: 0,
                      }}
                      statusFilter={statusFilter}
                      search={search}
                      isInterviewPack
                      questions={interviewPack}
                    />
                  </section>
                </div>
              </div>
              <div className="hidden w-72 shrink-0 lg:block">
                <div className="sticky top-28">
                  <ReportSidebar
                    score={score ?? 0}
                    lastAnalyzed={formatDate(report.updated_at ?? report.created_at)}
                    commitSha={report.commit_sha}
                    highlights={highlights}
                    topIssues={topIssues}
                    nextActions={nextActions}
                  />
                </div>
              </div>
            </div>
          </Container>
        </>
      )}
    </Page>
  );
}
