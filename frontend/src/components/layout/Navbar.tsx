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
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
      <Container className="flex h-16 items-center justify-between">
        <Link
          href="/"
          className="font-heading flex items-center gap-2 text-lg font-semibold tracking-tight text-slate-900"
        >
          HireLens
          <span className="rounded-md bg-accent/10 px-2 py-0.5 text-xs font-medium text-accent">
            Beta
          </span>
        </Link>
        <nav className="flex items-center gap-6">
          <button
            type="button"
            onClick={() => scrollTo("features")}
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            Features
          </button>
          <button
            type="button"
            onClick={() => scrollTo("example")}
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            Example
          </button>
          <button
            type="button"
            onClick={() => scrollTo("how-it-works")}
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            How it works
          </button>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            GitHub
          </a>
          {showTryCta && (
            <Button onClick={() => scrollTo("get-started")}>
              Try it now
            </Button>
          )}
        </nav>
      </Container>
    </header>
  );
}
