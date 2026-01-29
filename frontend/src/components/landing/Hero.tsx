"use client";

import { Container } from "@/components/layout/Container";
import { AnalyzeForm } from "@/components/landing/AnalyzeForm";

export function Hero() {
  function scrollToExample() {
    document.getElementById("example")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <section
      id="analyze"
      className="relative scroll-mt-14 flex min-h-[100svh] flex-col items-center justify-center pt-12 pb-10 lg:pb-12"
    >
      {/* Subtle overlay: very faint radial gradient for depth */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(9, 105, 218, 0.15), transparent 60%)",
        }}
        aria-hidden
      />
      <Container className="relative">
        <div className="mx-auto flex max-w-2xl flex-col items-center text-center">
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
            REPOSITORY READINESS
          </p>
          <h1 className="font-heading mt-1.5 max-w-xl text-[2.5rem] font-semibold leading-tight tracking-tight text-[var(--text)] sm:text-5xl lg:text-[3.5rem]">
            Repository readiness in 60 seconds
          </h1>
          <p className="mt-2 max-w-xl text-base leading-relaxed text-[var(--muted)]">
            Runability, CI, security signals-summarized into a shareable report.
          </p>
          <div className="mt-4 w-full max-w-xl sm:mt-5">
            <AnalyzeForm />
          </div>
          <p className="mt-2 text-xs text-[var(--muted)] sm:mt-3">
            Read-only • No code execution • No login • Shareable report link
          </p>
          <button
            type="button"
            onClick={scrollToExample}
            className="mt-1.5 text-xs text-[var(--muted)] transition-colors hover:text-[var(--link)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2 rounded"
          >
            See example report →
          </button>
        </div>
      </Container>
    </section>
  );
}
