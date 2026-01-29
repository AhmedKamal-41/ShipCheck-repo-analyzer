import { Check } from "lucide-react";
import {
  Wrench,
  Users,
  GitBranch,
  GraduationCap,
} from "lucide-react";
import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";

const TRUSTED_ITEMS = [
  { icon: Wrench, label: "Engineers" },
  { icon: Users, label: "Recruiters" },
  { icon: GitBranch, label: "Teams" },
  { icon: GraduationCap, label: "Open Source" },
] as const;

const CHECKLIST_ITEMS = [
  "Runability",
  "CI & tests",
  "Security signals",
  "Interview pack",
] as const;

export function TrustedBy() {
  return (
    <CenteredSection id="trusted-by" className="scroll-mt-20">
      <Container>
        <div className="mx-auto max-w-6xl">
          <p className="text-center text-xs font-medium uppercase tracking-wider text-slate-400">
            TRUSTED BY
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-8 sm:gap-10 md:gap-12">
            {TRUSTED_ITEMS.map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex flex-col items-center gap-2 text-slate-600"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-500">
                  <Icon className="h-5 w-5" aria-hidden />
                </div>
                <span className="text-sm font-medium text-slate-700">
                  {label}
                </span>
              </div>
            ))}
          </div>
          <ul className="mx-auto mt-10 flex max-w-2xl flex-col items-center gap-3 sm:gap-4">
            {CHECKLIST_ITEMS.map((item) => (
              <li
                key={item}
                className="flex items-center gap-2 text-base text-slate-700"
              >
                <Check
                  className="h-5 w-5 shrink-0 text-accent"
                  aria-hidden
                />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </Container>
    </CenteredSection>
  );
}
