"use client";

import { AnalyzeForm } from "./AnalyzeForm";
import { LandingSection } from "./LandingSection";
import { LandingSectionHeader } from "./LandingSectionHeader";

export function FinalCta() {
  return (
    <LandingSection id="final-cta" bg="bg">
      <LandingSectionHeader
        eyebrow="Get started"
        title="Score a repo now."
        align="center"
      />

      <div className="mx-auto mt-10 w-full max-w-xl">
        <AnalyzeForm />
        <p className="mt-3 text-center text-sm text-[var(--muted)]">
          No signup. No login. Free.
        </p>
      </div>
    </LandingSection>
  );
}
