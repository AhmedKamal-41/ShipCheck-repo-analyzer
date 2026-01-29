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
import { Page } from "@/components/layout/Page";
import { Navbar } from "@/components/layout/Navbar";
import { Container } from "@/components/layout/Container";
import { Card } from "@/components/ui/Card";
import { ReportHeader } from "@/components/report/ReportHeader";
import { ScoreSummary } from "@/components/report/ScoreSummary";
import { ChecksSection } from "@/components/report/ChecksSection";
import { ReportSkeleton } from "@/components/report/ReportSkeleton";
import { ReportError } from "@/components/report/ReportError";

const POLL_INTERVAL_MS = 2000;
const POLL_DEADLINE_MS = 30000;

const TAB_IDS = [
  "Runability",
  "Engineering",
  "Security",
  "Docs",
  "Interview Pack",
] as const;

const SECTION_MAP: Record<string, string> = {
  Runability: "Runability",
  "Engineering Quality": "Engineering",
  "Secrets Safety": "Security",
  Documentation: "Docs",
};

function mapSectionToTab(s: SectionFinding): string {
  return SECTION_MAP[s.name] ?? s.name;
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
  // Reset pollTimedOut when id changes by using a key-based approach
  const [pollTimedOut, setPollTimedOut] = useState(false);
  const [statusFilter, setStatusFilter] = useState<"all" | "fail" | "warn" | "pass">("all");
  const [search, setSearch] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const idRef = useRef(id);

  // Reset poll timeout when id changes
  // This is safe as it's a controlled reset when the route param changes
  useEffect(() => {
    if (idRef.current !== id) {
      idRef.current = id;
      // eslint-disable-next-line react-hooks/set-state-in-effect
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

  const sectionByTab = useMemo(() => {
    const m: Record<string, SectionFinding | null> = {};
    for (const t of TAB_IDS) m[t] = null;
    for (const s of sections) {
      const tab = mapSectionToTab(s);
      if ((TAB_IDS as readonly string[]).includes(tab)) m[tab] = s;
    }
    return m;
  }, [sections]);

  if (err) {
    return (
      <Page>
        <Navbar showTryCta={false} />
        <Container className="py-12 lg:py-16">
          <div className="mx-auto max-w-md rounded-2xl border border-red-200 bg-red-50 p-6 text-center shadow-sm md:p-8">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
            </div>
            <p className="text-lg font-medium text-red-700" role="alert">{err}</p>
            <Link
              href="/"
              className="mt-4 inline-block text-sm font-medium text-red-700 underline hover:text-red-900"
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
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
            <div className="text-center">
              <p className="font-medium text-slate-700">Loading report…</p>
              <p className="text-sm text-slate-500">Please wait a moment.</p>
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
            <Container className="py-4">
              <p className="text-center text-sm text-slate-500">
                Still pending. Check back later or refresh.
              </p>
            </Container>
          )}
          <ReportSkeleton />
        </>
      )}

      {isFailed && (
        <ReportError
          message={errorMessage ?? "Analysis failed"}
          retrying={retrying}
          onRetry={handleReanalyze}
          retryError={retryError}
        />
      )}

      {isDone && (
        <>
          <ScoreSummary
            score={score ?? 0}
            lastAnalyzed={formatDate(report.updated_at ?? report.created_at)}
            commitSha={report.commit_sha}
            highlights={highlights}
          />
          <Container className="pb-16 pt-0">
            <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-3 lg:mb-8">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap gap-2">
                  {(["all", "fail", "warn", "pass"] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setStatusFilter(s)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                        statusFilter === s
                          ? "bg-slate-800 text-white"
                          : "bg-white text-slate-600 shadow-sm hover:bg-slate-100"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <input
                    type="search"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Filter checks…"
                    className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 shadow-sm placeholder-slate-400 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
                    aria-label="Filter checks or questions"
                  />
                </div>
              </div>
            </div>
            <p className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-500">
              Checks
            </p>
            <div className="space-y-6 lg:space-y-8">
              {TAB_IDS.map((tab) => {
                if (tab === "Interview Pack") {
                  return (
                    <ChecksSection
                      key={tab}
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
                  );
                }
                const sec = sectionByTab[tab];
                if (!sec) {
                  return (
                    <Card key={tab} className="hover:translate-y-0">
                      <h3 className="font-heading text-lg font-semibold text-slate-900">
                        {tab}
                      </h3>
                      <p className="mt-1 text-sm text-slate-500">
                        No data for this section.
                      </p>
                    </Card>
                  );
                }
                return (
                  <ChecksSection
                    key={tab}
                    section={sec}
                    statusFilter={statusFilter}
                    search={search}
                  />
                );
              })}
            </div>
          </Container>
        </>
      )}
    </Page>
  );
}
