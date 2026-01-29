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
    <header className="sticky top-14 z-10 border-b border-[#d0d7de] bg-white">
      <Container className="flex h-12 items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <Link
            href="/"
            className="shrink-0 text-sm font-medium text-[#57606a] hover:text-[#1f2328]"
          >
            ← Back
          </Link>
          <span className="hidden text-[#d0d7de] sm:inline">|</span>
          <a
            href={repoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="min-w-0 truncate text-sm font-medium text-[#1f2328] hover:text-[#0969da] hover:underline"
          >
            {repoLabel}
          </a>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button variant="secondary" onClick={onCopyLink} className="h-8 px-3 text-xs">
            <Copy className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{copied ? "Copied!" : "Copy link"}</span>
          </Button>
          <Button
            onClick={onReanalyze}
            disabled={retrying}
            className="h-8 px-3 text-xs"
          >
            {retrying ? <Spinner /> : <RotateCcw className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{retrying ? "Re-analyzing…" : "Re-run"}</span>
          </Button>
        </div>
      </Container>
    </header>
  );
}
