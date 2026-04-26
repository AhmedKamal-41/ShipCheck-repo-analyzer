import { Play, Shield, MessageCircleQuestion, Wrench } from "lucide-react";
import { LandingSection } from "./LandingSection";
import { LandingSectionHeader } from "./LandingSectionHeader";

const SECONDARY_FEATURES = [
  {
    icon: Play,
    title: "Runability",
    description: "README, install/run instructions, and common entrypoints.",
    chips: ["README", "run", "entrypoints"],
  },
  {
    icon: Shield,
    title: "Security",
    description:
      "Secrets scan and dependency hygiene. We surface what's present and missing.",
    chips: ["secrets", "deps", "hygiene"],
  },
  {
    icon: MessageCircleQuestion,
    title: "Interview Pack",
    description: "Tailored interview questions based on the repo.",
    chips: ["questions", "repo-based", "discussion"],
  },
] as const;

const PRIMARY_CHIPS = ["CI config", "tests", "lockfile", "lint", "coverage"] as const;

const CI_SNIPPET = `      - name: Run tests
        run: pytest --cov=app --cov-fail-under=80
      - name: Lint
        run: ruff check app`;

export function Features() {
  return (
    <LandingSection id="features" bg="bg">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] lg:gap-12">
        <LandingSectionHeader
          eyebrow="What we check"
          title="Six categories. Every check evidence-backed."
          subtitle="The rubric is the same for every repo. Every finding cites a file, a line range, and the rule that fired."
          align="left"
        />

        <div className="space-y-5">
          <article className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 transition-all duration-200 ease-out hover:border-[#8c959f] hover:shadow-md">
            <div className="flex items-center gap-2">
              <Wrench className="h-4 w-4 text-[var(--muted)]" aria-hidden />
              <h3 className="text-base font-semibold text-[var(--text)]">
                Engineering Quality
              </h3>
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[var(--muted)]">
              CI configuration, test layout, lint and format setup, dependency
              pinning. The strongest signal that a project is maintained, and
              the cheapest to fix when it&apos;s missing.
            </p>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-[1fr_minmax(0,1.1fr)] sm:items-start">
              <div className="flex flex-wrap gap-1.5">
                {PRIMARY_CHIPS.map((c) => (
                  <span
                    key={c}
                    className="inline-flex rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2 py-0.5 text-xs font-medium text-[var(--muted)]"
                  >
                    {c}
                  </span>
                ))}
              </div>
              <div>
                <p className="mb-1 text-xs text-[var(--muted)]">.github/workflows/ci.yml</p>
                <pre className="overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-3 font-mono text-xs leading-relaxed text-[var(--text)]">
                  {CI_SNIPPET}
                </pre>
              </div>
            </div>
          </article>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {SECONDARY_FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <article
                  key={f.title}
                  className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 transition-all duration-200 ease-out hover:-translate-y-0.5 hover:border-[#8c959f] hover:shadow-md"
                >
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-[var(--muted)]" aria-hidden />
                    <h3 className="text-sm font-semibold text-[var(--text)]">
                      {f.title}
                    </h3>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-[var(--muted)]">
                    {f.description}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {f.chips.map((c) => (
                      <span
                        key={c}
                        className="inline-flex rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2 py-0.5 text-[11px] font-medium text-[var(--muted)]"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </LandingSection>
  );
}
