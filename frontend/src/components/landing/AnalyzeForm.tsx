"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Github } from "lucide-react";
import { analyzeRepo } from "@/lib/api";
import { validateGitHubUrl } from "@/lib/validate";
import { Button } from "@/components/ui/Button";

function Spinner() {
  return (
    <div
      className="h-4 w-4 shrink-0 rounded-full border-2 border-white/40 border-t-white animate-spin"
      aria-hidden
    />
  );
}

export function AnalyzeForm() {
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
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow)]">
      <form onSubmit={handleSubmit} className="w-full">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative min-w-0 flex-1">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]">
              <Github className="h-4 w-4" aria-hidden />
            </span>
            <input
              ref={inputRef}
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              disabled={loading}
              className={`h-10 w-full rounded-lg border bg-[var(--surface)] px-3 pl-9 text-sm text-[var(--text)] placeholder-[var(--muted)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 disabled:opacity-60 ${
                error ? "border-[var(--danger)]" : "border-[var(--border)] focus:border-[var(--link)]"
              }`}
              aria-label="GitHub repository URL"
              aria-invalid={!!error}
            />
          </div>
          <Button
            type="submit"
            disabled={loading}
            className="h-10 shrink-0 sm:min-w-[120px]"
          >
            {loading ? (
              <>
                <Spinner />
                <span>Analyzing…</span>
              </>
            ) : (
              "Analyze"
            )}
          </Button>
        </div>
        {error && (
          <div
            className="mt-3 rounded-lg border border-[var(--danger)]/30 bg-[#ffebe9] px-3 py-2"
            role="alert"
          >
            <p className="text-sm text-[var(--danger)]">{error}</p>
          </div>
        )}
      </form>
    </div>
  );
}
