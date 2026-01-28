"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Github } from "lucide-react";
import { analyzeRepo } from "@/lib/api";
import { validateGitHubUrl } from "@/lib/validate";
import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";
import { Button } from "@/components/ui/Button";

const EXAMPLES = [
  { label: "vercel/next.js", url: "https://github.com/vercel/next.js" },
  { label: "tiangolo/fastapi", url: "https://github.com/tiangolo/fastapi" },
  { label: "pallets/flask", url: "https://github.com/pallets/flask" },
] as const;

function Spinner() {
  return (
    <div
      className="h-5 w-5 shrink-0 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin"
      aria-hidden
    />
  );
}

export function GetStarted() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const v = validateGitHubUrl(url);
    if (!v.valid) {
      setError(v.error);
      return;
    }
    setLoading(true);
    try {
      const { report_id } = await analyzeRepo(url);
      router.push(`/reports/${report_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setLoading(false);
    }
  }

  return (
    <CenteredSection id="get-started" className="scroll-mt-20">
      <Container>
        <CenteredSectionHeader
          title="Get started"
          subtitle="Paste a GitHub repo URL and we'll generate a report."
        />
        <div className="mx-auto max-w-3xl">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:rounded-3xl md:p-8">
            <form onSubmit={handleSubmit} className="mx-auto max-w-2xl">
              <div className="flex flex-col gap-3 sm:flex-row">
                <div className="relative min-w-0 flex-1">
                  <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
                    <Github className="h-5 w-5" aria-hidden />
                  </span>
                  <input
                    ref={inputRef}
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo"
                    disabled={loading}
                    className="h-12 w-full rounded-xl border border-slate-300 bg-white px-4 pl-12 text-base text-slate-900 shadow-sm placeholder-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:opacity-60 sm:h-14"
                    aria-label="GitHub repository URL"
                  />
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  className="shrink-0 sm:min-w-[160px]"
                >
                  {loading ? (
                    <>
                      <Spinner />
                      <span>Generating…</span>
                    </>
                  ) : (
                    "Generate report"
                  )}
                </Button>
              </div>
              {error && (
                <div
                  className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3"
                  role="alert"
                >
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                {EXAMPLES.map(({ label, url: u }) => (
                  <button
                    key={u}
                    type="button"
                    onClick={() => {
                      setUrl(u);
                      setError(null);
                      inputRef.current?.focus();
                    }}
                    className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-100"
                  >
                    {label}
                  </button>
                ))}
              </div>
            </form>
          </div>
        </div>
      </Container>
    </CenteredSection>
  );
}
