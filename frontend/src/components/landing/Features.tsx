import {
  Play,
  Wrench,
  Shield,
  MessageCircleQuestion,
} from "lucide-react";
import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";
import { Card } from "@/components/ui/Card";

const FEATURES = [
  {
    icon: Play,
    title: "Runability",
    description:
      "README, install/run instructions, and common entrypoints.",
    includes: ["README", "run", "entrypoints"],
  },
  {
    icon: Wrench,
    title: "Engineering & CI",
    description:
      "CI config, test layout, dependency lockfiles. No code execution.",
    includes: ["CI config", "tests", "lockfile"],
  },
  {
    icon: Shield,
    title: "Security",
    description:
      "Secrets safety and dependency hygiene. We surface what's present and missing.",
    includes: ["secrets", "deps", "hygiene"],
  },
  {
    icon: MessageCircleQuestion,
    title: "Interview Pack",
    description:
      "Tailored interview questions based on the repo.",
    includes: ["questions", "repo-based", "discussion"],
  },
] as const;

export function Features() {
  return (
    <CenteredSection id="features" className="scroll-mt-20 pt-12 sm:pt-20">
      <Container>
        <CenteredSectionHeader
          title="What we check"
          subtitle="Four areas that matter for interview readiness."
        />
        <p className="mb-6 text-center text-sm text-[var(--muted)]">
          Supports: Next.js • FastAPI • Flask
        </p>
        <div className="mx-auto grid max-w-5xl grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <Card
                key={f.title}
                className="flex h-full flex-col gap-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md hover:border-[#8c959f]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--surface-2)] text-[var(--muted)]">
                  <Icon className="h-5 w-5" aria-hidden />
                </div>
                <h3 className="text-base font-semibold text-[var(--text)]">
                  {f.title}
                </h3>
                <p className="flex-1 text-sm text-[var(--muted)] leading-relaxed">
                  {f.description}
                </p>
                <div>
                  <p className="mb-1.5 text-xs font-medium text-[var(--muted)]">
                    Includes:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {f.includes.map((item) => (
                      <span
                        key={item}
                        className="inline-flex rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--muted)] transition-colors hover:bg-[#eaeef2]"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </Container>
    </CenteredSection>
  );
}
