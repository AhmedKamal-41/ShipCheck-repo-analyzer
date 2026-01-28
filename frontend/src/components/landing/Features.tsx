import {
  Play,
  Wrench,
  MessageCircleQuestion,
} from "lucide-react";
import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { Card } from "@/components/ui/Card";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";

const FEATURES = [
  {
    icon: Play,
    title: "Runability",
    description:
      "Can you run the app from a clean clone? We check README, install and run instructions, and common entrypoints.",
  },
  {
    icon: Wrench,
    title: "Engineering & Security",
    description:
      "CI config, test layout, dependency lockfiles, and structure. Secrets safety and dependency hygiene. We surface what's present and what's missing—no code execution.",
  },
  {
    icon: MessageCircleQuestion,
    title: "Interview Pack",
    description:
      "Tailored interview questions based on the repo so you can discuss what's actually in the codebase.",
  },
] as const;

export function Features() {
  return (
    <CenteredSection id="features" className="scroll-mt-20">
      <Container>
        <CenteredSectionHeader
          title="What we check"
          subtitle="Three areas that matter for interview readiness."
        />
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 lg:gap-8">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            return (
              <Card key={f.title} className="flex h-full flex-col">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-600">
                  <Icon className="h-5 w-5" aria-hidden />
                </div>
                <h3 className="mt-4 font-semibold text-slate-900">{f.title}</h3>
                <p className="mt-2 flex-1 text-base text-slate-600 leading-relaxed">
                  {f.description}
                </p>
              </Card>
            );
          })}
        </div>
      </Container>
    </CenteredSection>
  );
}
