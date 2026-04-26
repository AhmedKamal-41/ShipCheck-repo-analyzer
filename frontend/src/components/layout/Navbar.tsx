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
          className="font-heading flex items-center text-base font-semibold tracking-tight text-[var(--text)]"
        >
          ShipCheck
        </Link>
        <nav className="flex items-center gap-5">
          <a
            href="#"
            className="border-b border-transparent pb-0.5 text-sm text-[var(--muted)] transition-colors duration-200 ease-out hover:border-current hover:text-[var(--text)] focus:outline-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            Docs
          </a>
          <button
            type="button"
            onClick={() => scrollTo("example")}
            className="border-b border-transparent pb-0.5 text-sm text-[var(--muted)] transition-colors duration-200 ease-out hover:border-current hover:text-[var(--text)] focus:outline-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
          >
            Example
          </button>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="border-b border-transparent pb-0.5 text-sm text-[var(--muted)] transition-colors duration-200 ease-out hover:border-current hover:text-[var(--text)] focus:outline-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
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
