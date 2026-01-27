"use client";

import { useRef } from "react";
import { Github } from "lucide-react";
import { Spinner } from "./Spinner";

const EXAMPLES = [
  "https://github.com/vercel/next.js",
  "https://github.com/tiangolo/fastapi",
  "https://github.com/pallets/flask",
] as const;

interface HeroInputCardProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  error: string | null;
  disabled?: boolean;
}

export function HeroInputCard({
  value,
  onChange,
  onSubmit,
  loading,
  error,
  disabled = false,
}: HeroInputCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="relative">
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">
            <Github className="h-5 w-5" aria-hidden />
          </span>
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="https://github.com/owner/repo"
            disabled={loading || disabled}
            className="w-full rounded-xl border border-slate-300 bg-slate-50/50 py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-500 transition-colors focus:border-accent focus:bg-white focus:outline-none focus:ring-2 focus:ring-accent/20 disabled:cursor-not-allowed disabled:opacity-60"
            aria-label="GitHub repository URL"
          />
        </div>
        <button
          type="submit"
          disabled={loading || disabled}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-3.5 px-4 font-semibold text-white transition-colors hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <Spinner />
              <span>Analyzing…</span>
            </>
          ) : (
            "Analyze"
          )}
        </button>
        <p className="text-center text-sm text-slate-500">
          Paste a public GitHub repo URL.
        </p>
        {error && (
          <div
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3"
            role="alert"
          >
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </form>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {EXAMPLES.map((url) => (
          <button
            key={url}
            type="button"
            onClick={() => {
              onChange(url);
              inputRef.current?.focus();
            }}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-100"
          >
            {url.replace("https://github.com/", "")}
          </button>
        ))}
      </div>
    </div>
  );
}
