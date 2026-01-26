"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  type CheckFinding,
  type Report,
  type SectionFinding,
  analyzeRepo,
  getReport,
  isFindingsFailed,
  isFindingsSuccess,
} from "@/lib/api";

function StatusBadge({ status }: { status: "pass" | "warn" | "fail" }) {
  const styles =
    status === "pass"
      ? "bg-green-100 text-green-800"
      : status === "warn"
        ? "bg-amber-100 text-amber-800"
        : "bg-red-100 text-red-800";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase ${styles}`}
    >
      {status}
    </span>
  );
}

function CheckRow({ check }: { check: CheckFinding }) {
  const { file, snippet } = check.evidence || { file: "—", snippet: "" };
  return (
    <div className="border-l-2 border-neutral-200 pl-3 py-2 space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-sm text-neutral-800">
          {check.name}
        </span>
        <StatusBadge status={check.status} />
      </div>
      {(file || snippet) && (
        <div className="text-xs text-neutral-600">
          {file && file !== "—" && (
            <p>
              <span className="font-medium">File:</span> {file}
            </p>
          )}
          {snippet && (
            <pre className="mt-1 p-2 bg-neutral-100 rounded overflow-x-auto text-neutral-700 font-mono whitespace-pre-wrap break-words max-h-24 overflow-y-auto">
              {snippet}
            </pre>
          )}
        </div>
      )}
      <p className="text-sm text-neutral-700">{check.recommendation}</p>
    </div>
  );
}

function SectionCard({ section }: { section: SectionFinding }) {
  return (
    <section className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold text-neutral-900 mb-3">
        {section.name}
      </h3>
      <ul className="space-y-2">
        {section.checks.map((c) => (
          <li key={c.id}>
            <CheckRow check={c} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function Spinner() {
  return (
    <div
      className="h-6 w-6 rounded-full border-2 border-neutral-300 border-t-neutral-600 animate-spin"
      aria-hidden
    />
  );
}

const POLL_INTERVAL_MS = 2000;
const POLL_DEADLINE_MS = 30000;

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

  const handleRetry = useCallback(() => {
    if (!report?.repo_url || retrying) return;
    setRetryError(null);
    setRetrying(true);
    analyzeRepo(report.repo_url)
      .then((data) => router.push(`/reports/${data.report_id}`))
      .catch((e) => {
        setRetryError(e instanceof Error ? e.message : "Retry failed");
        setRetrying(false);
      });
  }, [report, retrying, router]);

  const isDone = report?.status === "done";
  const isFailed = report?.status === "failed";
  const isPending = report?.status === "pending";
  const findings = report?.findings_json ?? null;
  const successFindings = isFindingsSuccess(findings) ? findings : null;
  const failedFindings = isFindingsFailed(findings) ? findings : null;
  const sections: SectionFinding[] =
    successFindings?.sections?.length ? successFindings.sections : [];
  const score =
    successFindings?.overall_score ?? report?.overall_score ?? null;
  const errorMessage = failedFindings?.error ?? null;

  const repoLabel =
    report?.repo_owner && report?.repo_name
      ? `${report.repo_owner}/${report.repo_name}`
      : report?.repo_url ?? "—";

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <main className="w-full max-w-2xl mx-auto px-6 py-10">
        {err && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200">
            <p className="text-red-700" role="alert">
              {err}
            </p>
            <Link
              href="/"
              className="inline-block mt-2 text-red-700 hover:text-red-900 underline"
            >
              Back to Home
            </Link>
          </div>
        )}

        {!report && !err && (
          <p className="text-neutral-500">Loading…</p>
        )}

        {report && !err && (
          <>
            <header className="mb-8">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-semibold text-neutral-900 mb-1">
                    Report
                  </h1>
                  <a
                    href={report.repo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-neutral-600 hover:text-neutral-900 hover:underline"
                  >
                    {repoLabel}
                  </a>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={copyShareLink}
                    className="px-3 py-1.5 rounded-lg border border-neutral-300 bg-white text-neutral-700 text-sm font-medium hover:bg-neutral-50 transition-colors"
                  >
                    {copied ? "Copied!" : "Copy share link"}
                  </button>
                  <Link
                    href="/"
                    className="text-neutral-700 hover:text-neutral-900 underline text-sm"
                  >
                    Analyze another repo
                  </Link>
                </div>
              </div>
            </header>

            <div className="mb-8">
              {isDone && score != null && (
                <div className="text-center py-6">
                  <p className="text-5xl font-bold text-neutral-900">
                    {score}
                  </p>
                  <p className="text-sm text-neutral-500 mt-1">Overall score</p>
                </div>
              )}
              {isPending && (
                <div className="py-4 flex flex-col items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Spinner />
                    <span className="text-neutral-600">
                      Analysis pending…
                    </span>
                  </div>
                  {pollTimedOut && (
                    <p className="text-sm text-neutral-500">
                      Still pending. Check back later or refresh.
                    </p>
                  )}
                </div>
              )}
              {isFailed && (
                <div className="py-4">
                  <p className="font-medium text-red-700">Analysis failed</p>
                  {errorMessage && (
                    <p className="text-sm text-neutral-600 mt-1">
                      {errorMessage}
                    </p>
                  )}
                  <button
                    type="button"
                    onClick={handleRetry}
                    disabled={retrying}
                    className="mt-3 px-4 py-2 rounded-lg bg-neutral-900 text-white text-sm font-medium hover:bg-neutral-800 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                  >
                    {retrying ? "Retrying…" : "Retry"}
                  </button>
                  {retryError && (
                    <p className="mt-2 text-sm text-red-600" role="alert">
                      {retryError}
                    </p>
                  )}
                </div>
              )}
            </div>

            {isDone && (
              <div className="space-y-6">
                {sections.length > 0 &&
                  sections.map((sec) => (
                    <SectionCard key={sec.name} section={sec} />
                  ))}
                {successFindings?.interview_pack &&
                  successFindings.interview_pack.length > 0 && (
                    <section className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
                      <h3 className="text-lg font-semibold text-neutral-900 mb-3">
                        Interview Pack
                      </h3>
                      <ol className="list-decimal list-inside space-y-2 text-neutral-700">
                        {successFindings.interview_pack.map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </ol>
                    </section>
                  )}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
