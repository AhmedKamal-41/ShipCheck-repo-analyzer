import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";

const STEPS = [
  {
    title: "Paste repo URL",
    description:
      "Enter any public GitHub repository link. We only read metadata and key files—no code execution.",
  },
  {
    title: "We scan key files",
    description:
      "Runability, tests and CI, dependency hygiene, and security signals are analyzed in seconds.",
  },
  {
    title: "Get your report",
    description:
      "Score, breakdown, evidence snippets, and interview questions. Share the link or run again anytime.",
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
        <div className="relative mx-auto max-w-5xl px-4 sm:px-6">
          <div className="flex justify-between">
            {STEPS.map((step, i) => (
              <div
                key={step.title}
                className="relative z-10 flex flex-1 flex-col items-center"
              >
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-accent bg-white text-base font-semibold text-accent sm:h-14 sm:w-14 sm:text-lg">
                  {i + 1}
                </div>
                <p className="mt-3 text-center text-sm font-semibold text-slate-900 sm:text-base">
                  {step.title}
                </p>
                <p className="mt-1 max-w-[200px] text-center text-sm text-slate-600 sm:max-w-[220px]">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
          <div
            className="absolute inset-x-[15%] top-6 border-t-2 border-slate-200 sm:top-7"
            aria-hidden
          />
        </div>
      </Container>
    </CenteredSection>
  );
}
