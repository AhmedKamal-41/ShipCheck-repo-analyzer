"use client";

import { Shield } from "lucide-react";
import { Container } from "@/components/layout/Container";
import { Button } from "@/components/ui/Button";

export function Hero() {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="pt-20 pb-16 md:pt-24 md:pb-20 lg:pt-28 lg:pb-24">
      <Container>
        <div className="mx-auto flex max-w-4xl flex-col items-center text-center">
          <p className="text-sm font-medium uppercase tracking-wider text-slate-500">
            Repository readiness
          </p>
          <h1 className="font-heading mt-2 text-4xl font-semibold leading-[1.05] tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            Know if a repo is interview-ready in 60 seconds.
          </h1>
          <p className="mt-4 max-w-xl text-base text-slate-600 leading-relaxed sm:text-lg">
            Runability, tests and CI, dependency hygiene, and security
            signals—summarized into a shareable report.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button onClick={() => scrollTo("get-started")}>
              Try it now
            </Button>
            <Button variant="secondary" onClick={() => scrollTo("example")}>
              See example
            </Button>
          </div>
          <div className="mt-6 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-3">
            <Shield className="h-5 w-5 shrink-0 text-slate-500" aria-hidden />
            <p className="text-sm text-slate-600">
              Read-only analysis. No code execution.
            </p>
          </div>
        </div>
      </Container>
    </section>
  );
}
