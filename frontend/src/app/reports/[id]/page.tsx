"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Copy, RotateCcw, ChevronLeft, Search } from "lucide-react";
import { motion } from "framer-motion";
import {
  type CheckFinding,
  type Report,
  type SectionFinding,
  analyzeRepo,
  getReport,
  isFindingsFailed,
  isFindingsSuccess,
} from "@/lib/api";
import { Spinner } from "@/components/Spinner";
import { ScoreCard } from "@/components/ScoreCard";
import { CheckItem } from "@/components/CheckItem";
import { SkeletonReport } from "@/components/SkeletonReport";
import { PageShell } from "@/components/PageShell";

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

function mapSectionToTab(section: SectionFinding): (typeof TAB_IDS)[number] {
  return (SECTION_MAP[section.name] ?? section.name) as (typeof TAB_IDS)[number];
}

function computeHighlights(
  sections: SectionFinding[],
  limit = 5
): string[] {
  const bullets: string[] = [];
  const fail: CheckFinding[] = [];
  const warn: CheckFinding[] = [];
  const pass: CheckFinding[] = [];
  for (const s of sections) {
    for (const c of s.checks) {
      if (c.status === "fail") fail.push(c);
      else if (c.status === "warn") warn.push(c);
      else pass.push(c);
    }
  }
  const ordered = [...fail, ...warn, ...pass];
  for (let i = 0; i < ordered.length && bullets.length < limit; i++) {
    const c = ordered[i];
    const short =
      c.status === "pass"
        ? `${c.name} detected`
        : c.status === "fail"
          ? `${c.name} missing`
          : `${c.name} (review)`;
    bullets.push(short);
  }
  return bullets;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, {
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
  const [activeTab, setActiveTab] = useState<(typeof TAB_IDS)[number]>("Runability");
  const [statusFilter, setStatusFilter] = useState<"all" | "fail" | "warn" | "pass">("all");
  const [search, setSearch] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!id) return;
    queueMicrotask(() => setPollTimedOut(false));
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
    () => (successFindings?.sections?.length ? successFindings.sections : []),
    [successFindings]
  );
  const score =
    successFindings?.overall_score ?? report?.overall_score ?? null;
  const errorMessage = failedFindings?.error ?? null;
  const interviewPack = useMemo(
    () => successFindings?.interview_pack ?? [],
    [successFindings]
  );

  const repoLabel =
    report?.repo_owner && report?.repo_name
      ? `${report.repo_owner}/${report.repo_name}`
      : report?.repo_url ?? "—";

  const highlights = useMemo(
    () => computeHighlights(sections),
    [sections]
  );

  const sectionByTab = useMemo(() => {
    const m: Record<string, SectionFinding | null> = {};
    for (const t of TAB_IDS) m[t] = null;
    for (const s of sections) {
      const tab = mapSectionToTab(s);
      if (TAB_IDS.includes(tab)) m[tab] = s;
    }
    return m;
  }, [sections]);

  const filteredChecks = useMemo(() => {
    const sec = activeTab === "Interview Pack" ? null : sectionByTab[activeTab];
    if (!sec) return [];
    let list = sec.checks;
    if (statusFilter !== "all") {
      list = list.filter((c) => c.status === statusFilter);
    }
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (c) =>
          c.name.toLowerCase().includes(q) ||
          (c.recommendation || "").toLowerCase().includes(q) ||
          (c.evidence?.snippet || "").toLowerCase().includes(q) ||
          (c.evidence?.file || "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [activeTab, sectionByTab, statusFilter, search]);

  const filteredQuestions = useMemo(() => {
    if (activeTab !== "Interview Pack") return [];
    const q = search.trim().toLowerCase();
    if (!q) return interviewPack;
    return interviewPack.filter((line) =>
      line.toLowerCase().includes(q)
    );
  }, [activeTab, interviewPack, search]);

  if (err) {
    return (
      <div className="min-h-[calc(100vh-3.5rem)]">
        <PageShell className="py-12">
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <p className="text-red-700" role="alert">
              {err}
            </p>
            <Link
              href="/"
              className="mt-2 inline-block text-red-700 underline hover:text-red-900"
            >
              Back to Home
            </Link>
          </div>
        </PageShell>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-[calc(100vh-3.5rem)]">
        <PageShell className="py-12">
          <div className="flex items-center gap-2 text-slate-500">
            <Spinner />
            <span>Loading report…</span>
          </div>
        </PageShell>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] text-slate-900">
      <header className="sticky top-14 z-10 border-b border-slate-200 bg-white/95 backdrop-blur-sm">
        <PageShell className="flex flex-wrap items-center justify-between gap-4 py-3">
          <Link
            href="/"
            className="flex items-center gap-1 text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden />
            Analyze another repo
          </Link>
          <a
            href={report.repo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate font-medium text-slate-900 hover:text-accent hover:underline"
          >
            {repoLabel}
          </a>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={copyShareLink}
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              <Copy className="h-4 w-4" aria-hidden />
              {copied ? "Copied!" : "Copy share link"}
            </button>
            <button
              type="button"
              onClick={handleReanalyze}
              disabled={retrying}
              className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-accent/90 disabled:opacity-60"
            >
              {retrying ? <Spinner /> : <RotateCcw className="h-4 w-4" aria-hidden />}
              {retrying ? "Re-analyzing…" : "Re-analyze"}
            </button>
          </div>
        </PageShell>
      </header>

      <main className="pb-16">
        {isPending && (
          <PageShell className="py-12">
            <div className="mb-6 flex flex-col items-center gap-3">
              <div className="flex items-center gap-2">
                <Spinner />
                <span className="text-slate-600">Analysis in progress…</span>
              </div>
              {pollTimedOut ? (
                <p className="text-sm text-slate-500">
                  Still pending. Check back later or refresh.
                </p>
              ) : (
                <p className="text-sm text-slate-500">
                  This may take a few seconds.
                </p>
              )}
            </div>
            <SkeletonReport />
          </PageShell>
        )}

        {isFailed && (
          <PageShell className="py-12">
            <div className="mx-auto max-w-md rounded-xl border border-red-200 bg-red-50 p-6 text-center">
              <p className="font-medium text-red-700">Analysis failed</p>
              {errorMessage && (
                <p className="mt-1 text-sm text-slate-600">{errorMessage}</p>
              )}
              <button
                type="button"
                onClick={handleReanalyze}
                disabled={retrying}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-2.5 font-medium text-white hover:bg-accent/90 disabled:opacity-60"
              >
                {retrying ? <Spinner /> : null}
                {retrying ? "Retrying…" : "Retry"}
              </button>
              {retryError && (
                <p className="mt-2 text-sm text-red-600" role="alert">
                  {retryError}
                </p>
              )}
            </div>
          </PageShell>
        )}

        {isDone && (
          <PageShell maxWidth="4xl" className="py-8">
            <section className="mb-10 flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-around">
              <ScoreCard score={score ?? 0} />
              <div className="flex-1 space-y-2">
                {highlights.map((h, i) => (
                  <p key={i} className="text-sm text-slate-700">
                    • {h}
                  </p>
                ))}
              </div>
            </section>

            <div className="mb-4 flex flex-wrap items-center gap-2 text-sm text-slate-500">
              <span>Last analyzed: {formatDate(report.updated_at ?? report.created_at)}</span>
              {report.commit_sha && (
                <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs">
                  {report.commit_sha.slice(0, 7)}
                </span>
              )}
            </div>

            <div
              role="tablist"
              aria-label="Report sections"
              className="mb-4 flex flex-wrap gap-2 overflow-x-auto pb-2"
            >
              {TAB_IDS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab}
                  onClick={() => setActiveTab(tab)}
                  className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? "bg-accent text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="mb-4 flex flex-wrap items-center gap-2">
              {activeTab !== "Interview Pack" && (
                <div className="flex flex-wrap gap-1">
                  {(["all", "fail", "warn", "pass"] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setStatusFilter(s)}
                      className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize ${
                        statusFilter === s
                          ? "bg-slate-800 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <div className="relative min-w-[160px] flex-1 max-w-xs">
                <Search
                  className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
                  aria-hidden
                />
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Filter…"
                  className="w-full rounded-lg border border-slate-300 bg-white py-1.5 pl-8 pr-3 text-sm text-slate-900 placeholder-slate-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                  aria-label="Filter checks or questions"
                />
              </div>
            </div>

            <div role="tabpanel" className="space-y-3">
              {activeTab === "Interview Pack" ? (
                <motion.ol
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="list-inside list-decimal space-y-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  {filteredQuestions.length === 0 ? (
                    <li className="text-slate-500">No questions match the filter.</li>
                  ) : (
                    filteredQuestions.map((q, i) => (
                      <li key={i} className="pl-1 text-slate-700">
                        {q}
                      </li>
                    ))
                  )}
                </motion.ol>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="space-y-3"
                >
                  {filteredChecks.length === 0 ? (
                    <p className="rounded-xl border border-slate-200 bg-slate-50 py-8 text-center text-slate-500">
                      No checks match the filter.
                    </p>
                  ) : (
                    filteredChecks.map((c) => (
                      <CheckItem key={c.id} check={c} />
                    ))
                  )}
                </motion.div>
              )}
            </div>
          </PageShell>
        )}
      </main>
    </div>
  );
}
