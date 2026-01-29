"use client";

import Link from "next/link";
import { Container } from "./Container";
import { Button } from "@/components/ui/Button";

interface NavbarProps {
  showTryCta?: boolean;
}

export function Navbar({ showTryCta = true }: NavbarProps) {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <header className="sticky top-0 z-10 border-b border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur-sm">
      <Container className="flex h-14 items-center justify-between">
        <Link
          href="/"
          className="font-heading flex items-center gap-2 text-base font-semibold tracking-tight text-[var(--text)]"
        >
          HireLens
          <span className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--muted)]">
            Beta
          </span>
        </Link>
        <nav className="flex items-center gap-4">
          <a
            href="#"
            className="rounded text-sm text-[var(--muted)] transition-colors hover:text-[var(--link)] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            Docs
          </a>
          <button
            type="button"
            onClick={() => scrollTo("example")}
            className="rounded text-sm text-[var(--muted)] transition-colors hover:text-[var(--link)] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            Example
          </button>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded text-sm text-[var(--muted)] transition-colors hover:text-[var(--link)] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            GitHub
          </a>
          {showTryCta && (
            <Button onClick={() => scrollTo("analyze")}>
              Analyze
            </Button>
          )}
        </nav>
      </Container>
    </header>
  );
}
