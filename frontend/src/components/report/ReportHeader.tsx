"use client";

import Link from "next/link";
import { Copy, RotateCcw } from "lucide-react";
import { Container } from "@/components/layout/Container";
import { Button } from "@/components/ui/Button";

function Spinner() {
  return (
    <div
      className="h-4 w-4 shrink-0 rounded-full border-2 border-white/40 border-t-white animate-spin"
      aria-hidden
    />
  );
}

interface ReportHeaderProps {
  repoLabel: string;
  repoUrl: string;
  copied: boolean;
  retrying: boolean;
  onCopyLink: () => void;
  onReanalyze: () => void;
}

export function ReportHeader({
  repoLabel,
  repoUrl,
  copied,
  retrying,
  onCopyLink,
  onReanalyze,
}: ReportHeaderProps) {
  return (
    <header className="sticky top-16 z-10 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
      <Container className="flex h-14 items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <Link
            href="/"
            className="shrink-0 text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            ← Back
          </Link>
          <span className="hidden text-slate-300 sm:inline">|</span>
          <a
            href={repoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="min-w-0 truncate font-medium text-slate-900 hover:text-accent hover:underline"
          >
            {repoLabel}
          </a>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button variant="secondary" onClick={onCopyLink} className="h-9 px-3 text-sm">
            <Copy className="h-4 w-4" />
            <span className="hidden sm:inline">{copied ? "Copied!" : "Copy link"}</span>
          </Button>
          <Button
            onClick={onReanalyze}
            disabled={retrying}
            className="h-9 px-3 text-sm"
          >
            {retrying ? <Spinner /> : <RotateCcw className="h-4 w-4" />}
            <span className="hidden sm:inline">{retrying ? "Re-analyzing…" : "Re-analyze"}</span>
          </Button>
        </div>
      </Container>
    </header>
  );
}
