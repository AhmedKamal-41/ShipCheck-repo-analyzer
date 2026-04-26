"use client";

import { Container } from "@/components/layout/Container";
import { AnalyzeForm } from "@/components/landing/AnalyzeForm";

const STATS = [
  { value: "174", label: "Checks per analysis" },
  { value: "12s", label: "Avg report time" },
] as const;

export function Hero() {
  function scrollToExample() {
    document.getElementById("example")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <section
      id="analyze"
      className="relative scroll-mt-14 flex min-h-[70svh] items-center pt-12 pb-10 lg:pb-12"
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(9, 105, 218, 0.15), transparent 60%)",
        }}
        aria-hidden
      />
      <Container className="relative">
        <div className="grid grid-cols-1 items-center gap-10 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] md:gap-12 lg:gap-16">
          <div className="flex flex-col items-start text-left">
            <h1 className="font-heading max-w-xl text-[2.5rem] font-semibold leading-[1.05] tracking-tight text-[var(--text)] sm:text-5xl lg:text-[3.5rem]">
              Score any GitHub repo in 60 seconds.
            </h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-[var(--muted)]">
              Static analysis across runability, security, CI, and architecture.
              No execution, no login.{" "}
              <span className="mono-inline">174</span> checks per repo.
            </p>
            <div className="mt-6 w-full max-w-xl">
              <AnalyzeForm />
            </div>
            <p className="mt-3 text-xs text-[var(--muted)]">
              Read-only · No code execution · No login · Shareable report link
            </p>
            <button
              type="button"
              onClick={scrollToExample}
              className="mt-2 rounded text-xs text-[var(--muted)] transition-colors hover:text-[var(--link)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-2"
            >
              See example report →
            </button>
          </div>

          <aside
            className="grid w-full grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-1 md:gap-x-0 md:gap-y-10 md:border-l md:border-[var(--border)] md:pl-10 lg:pl-12"
            aria-label="ShipCheck stats"
          >
            {STATS.map((s) => (
              <div key={s.label} className="flex flex-col">
                <span className="display-stat">{s.value}</span>
                <span className="eyebrow mt-2">{s.label}</span>
              </div>
            ))}
          </aside>
        </div>
      </Container>
    </section>
  );
}
