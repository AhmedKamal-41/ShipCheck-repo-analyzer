import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";
import { Card } from "@/components/ui/Card";

const STEPS = [
  {
    title: "Paste repo URL",
    description:
      "Enter any public GitHub link. We only read metadata and key files.",
  },
  {
    title: "We scan key files",
    description:
      "Runability, CI, dependency hygiene, and security—analyzed in seconds.",
  },
  {
    title: "Get your report",
    description:
      "Score, evidence snippets, and interview questions. Share or re-run anytime.",
  },
] as const;

export function HowItWorks() {
  return (
    <CenteredSection id="how-it-works" className="scroll-mt-20">
      <Container>
        <CenteredSectionHeader
          title="How it works"
          subtitle="Three steps from URL to shareable report."
        />
        <div className="relative mx-auto max-w-4xl">
          {/* Connecting line (desktop): behind cards, thinner/lighter */}
          <div
            className="absolute left-0 right-0 top-6 z-0 hidden border-t border-[var(--border)]/60 sm:block"
            aria-hidden
          />
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-3 sm:gap-8">
            {STEPS.map((step, i) => (
              <Card
                key={step.title}
                className="relative z-10 text-center transition-shadow hover:border-[#8c959f] hover:shadow-md"
              >
                <div
                  className="relative z-10 mx-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--surface)] text-sm font-semibold text-[var(--muted)]"
                  style={{ width: "2rem", height: "2rem" }}
                >
                  {i + 1}
                </div>
                <p className="mt-3 text-sm font-semibold text-[var(--text)]">
                  {step.title}
                </p>
                <p className="mt-1 text-xs text-[var(--muted)] leading-relaxed">
                  {step.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </Container>
    </CenteredSection>
  );
}
